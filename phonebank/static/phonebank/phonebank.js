/*global
    $, libphonenumber, TelnyxWebRTC, JitsiMeetExternalAPI,
    agentName, googleFormUrl, jitsiRoom, jitsiServer
*/
/*jslint
    browser, devel, indent2, long, single
*/

var agentStats = '';
var currentCall = null;
var currentCallStartTime = null;
var currentCallTimerID = null;
var jitsiApi;
var telnyxClient = null;
var telnyxToken = null;

if (jitsiRoom) {
  const options = {
    configOverwrite: {startWithAudioMuted: true, startWithVideoMuted: true},
    height: $(window).height() - 100,
    parentNode: document.querySelector('#meet'),
    roomName: jitsiRoom,
    userInfo: {displayName: agentName}
  };
  jitsiApi = new JitsiMeetExternalAPI(jitsiServer, options);
} else {
  $('#meet').addClass('d-none');
}

$('#form').css('height', $(window).height() - 100);

function getContact(id = '') {
  const urlParams = new URLSearchParams(window.location.search);
  const key = urlParams.get('key');
  const path = 'api/voter/' + (id && encodeURIComponent(id) + '/') + '?key=' + encodeURIComponent(key);
  var similarVotersPending = false;
  $('#phones button').attr('disabled', true);
  $('#getContact').attr('disabled', true);
  $.getJSON(path, function (api) {
    $('#name').text(api.voter.name);
    $('#id').text('#' + api.voter.id);
    $('#statename').text(api.voter.statename);
    $('#notes').html(api.voter.notes);
    $('#phones').html('');
    Object.keys(api.voter.phones).forEach(function (phonetype) {
      const phone = api.voter.phones[phonetype];
      var icon;
      if (phonetype.includes('cell')) {
        icon = 'fa-mobile';
      } else {
        icon = 'fa-home';
      }
      if (phone[0] === '+') {
        const phoneNumber = parseInt(phone.substring(1));
        if (!Number.isNaN(phoneNumber)) {
          $('#phones').append('<button type="button" class="btn btn-outline-primary btn-sm" onclick="connectAndCall(\'+' + phoneNumber + '\')" id="phone' + phoneNumber + '"><i class="fa ' + icon + '" aria-hidden="true"></i> <small>' + libphonenumber.parsePhoneNumberFromString('+' + phoneNumber).format('NATIONAL') + '</small></button>');
        }
      }
    });
    if (api.similar_voters.length !== 0) {
      $('#similar_voters').html('<div class="alert alert-warning" role="alert"><p>Potential household members or duplicates:</p><ul></ul></div>');
      api.similar_voters.forEach(function (voter) {
        $('#similar_voters ul').append('<li><a class="link" role="button" title="' + voter.id.replaceAll('"', '') + '" onclick="getContact(\'' + voter.id.replaceAll('\'', '') + '\')"></a></li>');
        $('#similar_voters ul li:last a').text(voter.name);
        if (voter.provided) {
          $('#similar_voters ul li:last a').wrap('<strike>');
        } else {
          similarVotersPending = true;
        }
      });
    } else {
      $('#similar_voters').html('');
    }
    // When changing the iframe src or location.href, if there are
    // unsaved changes in the form, onbeforeunload will trigger an alert
    // about leaving the site. If this alert is canceled by the user, the
    // form will erroneously remain filled with the previous voter.
    // So to preempt this alert, we overwrite the entire iframe element.
    $("#formContainer").html('<iframe id="form" src="' + googleFormUrl + '?usp=pp_url&amp;entry.391576799=' + encodeURIComponent(api.voter.id) + '&amp;entry.1578854864=' + encodeURIComponent(Object.values(api.voter.phones).join(',')) + '&amp;entry.1498627907=' + encodeURIComponent(key) + '&amp;embedded=true' + '" width="100%" frameborder="0" marginheight="0" marginwidth="0" referrerpolicy="no-referrer">Loading…</iframe>');
    $('#form').css('height', $(window).height() - 100);
    agentStats = api.agent_stats;
  }).fail(function (jqxhr) {
    warning('Unable to fetch new contact: ' + (jqxhr.responseText || jqxhr.statusText));
  }).always(function () {
    if (!similarVotersPending) {
      $('#getContact').attr('disabled', false);
    }
    $('#phones button').attr('disabled', false);
  });
  $('#agentStats').text('');
}

// Adapted from https://github.com/team-telnyx/webrtc/blob/master/packages/js/examples/vanilla/index.html
function telnyxConnect() {
  telnyxClient = new TelnyxWebRTC.TelnyxRTC({
    login_token: telnyxToken
  });
  telnyxClient.remoteElement = 'audioCall';
  telnyxClient.on('telnyx.ready', function () {
    console.log('Telnyx ready');
  }).on('telnyx.socket.close', function () {
    console.log('Disconnected from Telnyx');
  }).on('telnyx.notification', handleNotification);
  console.log('Connecting to Telnyx');
  telnyxClient.connect();
}
function telnyxDisconnect() {
  console.log('Disconnecting from Telnyx');
  telnyxClient.disconnect();
}
function handleNotification(notification) {
  switch (notification.type) {
  case 'callUpdate':
    handleCallUpdate(notification.call);
    break;
  case 'vertoClientReady':
    break;
  default:
    warning(notification.type);
  }
}
function handleCallUpdate(call) {
  currentCall = call;
  $('#callStatus').text("Call " + call.state);
  switch (call.state) {
  case 'new': // Setup the UI
    break;
  case 'trying': // You are trying to call someone and he's ringing now
    break;
  case 'recovering': // Call is recovering from a previous session
    if (confirm('Recover the previous call?')) {
      currentCall.answer();
    } else {
      currentCall.hangup();
    }
    break;
  case 'ringing': // Someone is calling you
    //used to avoid alert block audio play, I delayed to audio play first.
    setTimeout(function () {
      if (confirm('Pick up the call?')) {
        currentCall.answer();
      } else {
        currentCall.hangup();
      }
    }, 1000);
    break;
  case 'active': // Call has become active
    $('#hangupCall').attr('disabled', true);
    currentCallStartTime = new Date();
    currentCallTimerID = setInterval(updateCallTimer, 500);
    break;
  case 'hangup': // Call is over
    break;
  case 'destroy': // Call has been destroyed
    $('#hangupCall').addClass('d-none');
    $('#hangupCall').attr('disabled', true);
    currentCall = null;
    clearInterval(currentCallTimerID);
    currentCallStartTime = null;
    $('#echo').attr('disabled', false);
    $('#getContact').attr('disabled', false);
    $('#callStatus').text('');
    $('#callTimer').text('');
    $('#agentStats').text(agentStats);
    if (call.causeCode === 21 || call.sipCode === 403) {
      // Equivalent to cause 'CALL_REJECTED' or sipReason 'Forbidden'.
      // Telnyx credentials may have been deleted. Try reconnecting later.
      telnyxDisconnect();
    }
    break;
  }
  const ignoreCauses = [undefined, 'NORMAL_CLEARING', 'PURGE'];
  const ignoreStates = ['destroy', 'purge'];
  if (ignoreCauses.indexOf(call.cause) === -1 && ignoreStates.indexOf(call.state) === -1) {
    $('#callLogContainer').removeClass('d-none');
    $('#callLog').append(document.createTextNode(call.cause + ' (' + call.sipCode + ' ' + call.sipReason + ')\n'));
  }
}

function connectAndCall(phone) {
  if (telnyxClient === null || !telnyxClient.connected) {
    const urlParams = new URLSearchParams(window.location.search);
    const key = urlParams.get('key');
    const path = 'api/voter/0/?key=' + encodeURIComponent(key);
    $.getJSON(path, function (api) {
      telnyxToken = api.telnyx_token;
      telnyxConnect();
      telnyxClient.on('telnyx.ready', function () {
        makeCall(phone);
      });
      agentStats = api.agent_stats;
    }).fail(function (jqxhr) {
      warning('Unable to place call: ' + (jqxhr.responseText || jqxhr.statusText));
    });
  } else {
    makeCall(phone);
  }
}

function makeCall(phone) {
  if (currentCall !== null) {
    warning("Call already ongoing");
    return;
  }
  if (jitsiRoom) {
    jitsiApi.isAudioMuted().then(function (muted) {
      if (!muted) {
        warning("Please mute conference audio during call");
      }
    });
  }
  const params = {
    audio: 1,
    destinationNumber: phone
  };
  if (phone[0] === '+') {
    const phoneNumber = parseInt(phone.substring(1));
    if (!Number.isNaN(phoneNumber)) {
      $('#phone' + phoneNumber).addClass('text-muted');
    }
  }
  $('#agentStats').text('');
  $('#callInfo').removeClass('d-none');
  $('#callLog').html('');
  $('#callLogContainer').addClass('d-none');
  currentCall = telnyxClient.newCall(params);
  currentCallStartTime = null;
  $('#getContact').attr('disabled', true);
  $('#echo').attr('disabled', true);
  $('#hangupCall').removeClass('d-none');
  $('#hangupCall').attr('disabled', false);
}

function updateCallTimer() {
  const elapsedTime = new Date() - currentCallStartTime;
  if (elapsedTime >= 7000) {
    $('#hangupCall').attr('disabled', false);
  }
  const mmss = new Date(elapsedTime).toISOString().slice(14, 19);
  $('#callTimer').text(mmss);
}

function warning(message) {
  console.warn(message);
  $('.alerts').append('<div class="alert alert-warning alert-dismissible fade show" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>');
  $('.alerts .alert:last').prepend(document.createTextNode(message));
  $('.alert-dismissible').alert();
}

$(document).ready(function () {
  $('#echo').attr('disabled', false);
  $('#getContact').attr('disabled', false);
});

$(document).keydown(function (e) {
  const digits = '0123456789#*';
  if (currentCall !== null && !e.originalEvent.repeat && digits.includes(e.key)) {
    currentCall.dtmf(e.key);
  }
});
