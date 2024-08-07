$( function() {
    $("#tabs ul li").click(function () {
        let activeTab = $(this).find("a").attr("href");
        let activeTabClass = activeTab.replace('#', '');
        $('.menu li ul li').each(function () {
            activeSubMenu($(this), activeTabClass)
        });
        if (activeTab == '#tools') {
            loadServices();
        } else if (activeTab == '#settings') {
            loadSettings();
        } else if (activeTab == '#updatehapwi') {
            loadupdatehapwi();
        } else if (activeTab == '#backup') {
            loadBackup();
        }
    });
} );
window.onload = function() {
	$('#tabs').tabs();
	let activeTabIdx = $('#tabs').tabs('option','active')
	if (cur_url.split('#')[0] == 'admin') {
		if (activeTabIdx == 6) {
			loadServices();
		} else if (activeTabIdx == 3) {
			loadSettings();
		} else if (activeTabIdx == 4) {
			loadBackup();
		} else if (activeTabIdx == 7) {
			loadupdatehapwi();
		}
	}
}
function updateService(service, action='update') {
	$("#ajax-update").html('')
	$("#ajax-update").html(wait_mess);
	$.ajax({
		url: "/admin/tools/update/" + service,
		success: function (data) {
			data = data.replace(/\s+/g, ' ');
			if (data.indexOf('Complete!') != '-1' || data.indexOf('Unpacking') != '-1') {
				toastr.clear();
				toastr.success(service + ' has been ' + action + 'ed');
			} else if (data.indexOf('Unauthorized') != '-1' || data.indexOf('Status code: 401') != '-1') {
				toastr.clear();
				toastr.error('It looks like there is no authorization in the Roxy-WI repository. Your subscription may have expired or there is no subscription. How to get the <b><a href="https://roxy-wi.org/pricing" title="Pricing" target="_blank">subscription</a></b>');
			} else if (data.indexOf('but not installed') != '-1') {
				toastr.clear();
				toastr.error('There is setting for Roxy-WI repository, but Roxy-WI is installed without repository. Please reinstall with package manager');
			} else if (data.indexOf('No Match for argument') != '-1' || data.indexOf('Unable to find a match') != '-1') {
				toastr.clear();
				toastr.error('It seems like Roxy-WI repository is not set. Please read docs for <b><a href="https://roxy-wi.org/updates">detail</a></b>');
			} else if (data.indexOf('password for') != '-1') {
				toastr.clear();
				toastr.error('It seems like apache user needs to be add to sudoers. Please read docs for <b><a href="https://roxy-wi.org/installation#ansible">detail</a></b>');
			} else if (data.indexOf('No packages marked for update') != '-1') {
				toastr.clear();
				toastr.info('It seems like the lastest version Roxy-WI is installed');
			} else if (data.indexOf('Connection timed out') != '-1') {
				toastr.clear();
				toastr.error('Cannot connect to Roxy-WI repository. Connection timed out');
			} else if (data.indexOf('--disable') != '-1') {
				toastr.clear();
				toastr.error('It seems like there is a problem with repositories');
			} else if (data.indexOf('Error: Package') != '-1') {
				toastr.clear();
				toastr.error(data);
			} else if (data.indexOf('conflicts with file from') != '-1') {
				toastr.clear();
				toastr.error(data);
			} else if (data.indexOf('error:') != '-1' || data.indexOf('Failed') != '-1') {
				toastr.error(data);
			} else if (data.indexOf('0 upgraded, 0 newly installed') != '-1') {
				toastr.info('There is no a new version of ' + service);
			} else {
				toastr.clear();
				toastr.success(service + ' has been ' + action + 'ed');
			}
			$("#ajax-update").html('');
			loadupdatehapwi();
			loadServices();
			show_version();
		}
	});
}
function loadSettings() {
	$.ajax({
		url: "/admin/settings",
		success: function (data) {
			data = data.replace(/\s+/g, ' ');
			if (data.indexOf('error:') != '-1') {
				toastr.error(data);
			} else {
				$('#settings').html(data);
				$.getScript(awesome);
				$( "input[type=checkbox]" ).checkboxradio();
				$( "select" ).selectmenu();
			}
		}
	} );
}
function loadServices() {
	$.ajax({
		url: "/admin/tools",
		success: function (data) {
			data = data.replace(/\s+/g, ' ');
			if (data.indexOf('danger') != '-1' || data.indexOf('unique') != '-1' || data.indexOf('error:') != '-1') {
				toastr.error(data);
			} else {
				$('#ajax-services-body').html(data);
				$.getScript(awesome);
			}
		}
	} );
}
function loadupdatehapwi() {
	$.ajax({
		url: "/admin/update",
		success: function (data) {
			data = data.replace(/\s+/g, ' ');
			if (data.indexOf('danger') != '-1' || data.indexOf('unique') != '-1' || data.indexOf('error:') != '-1') {
				toastr.error(data);
			} else {
				$('#ajax-updatehapwi-body').html(data);
			}
		}
	} );
}
function checkUpdateRoxy() {
	$.ajax({
		url: "/admin/update/check",
		success: function (data) {
			loadupdatehapwi();
		}
	} );
}
function confirmAjaxServiceAction(action, service) {
	let action_word = translate_div.attr('data-'+action);
	$( "#dialog-confirm-services" ).dialog({
		resizable: false,
		height: "auto",
		width: 400,
		modal: true,
		title: action_word + " " + service+"?",
		buttons: [{
			text: action_word,
			click: function () {
				$(this).dialog("close");
				ajaxActionServices(action, service);
			}
		}, {
			text: cancel_word,
			click: function() {
				$( this ).dialog( "close" );
			}
		}]
	});
}
function ajaxActionServices(action, service) {
	$.ajax( {
		url: "/admin/tools/action/" + service + "/" + action,
		success: function( data ) {
			if (data.indexOf('error:') != '-1' || data.indexOf('Failed') != '-1') {
				toastr.error(data);
			} else if (data.indexOf('warning: ') != '-1') {
				toastr.warning(data);
			} else {
				window.history.pushState("services", "services", cur_url[0].split("#")[0] + "#tools");
				toastr.success('The ' + service + ' has been ' + action +'ed');
				loadServices();
			}
		}
	} );
}
function showApacheLog(serv) {
	let rows = $('#rows').val();
	let grep = $('#grep').val();
	let exgrep = $('#exgrep').val();
	let hour = $('#time_range_out_hour').val();
	let minute = $('#time_range_out_minut').val();
	let hour1 = $('#time_range_out_hour1').val();
	let minute1 = $('#time_range_out_minut1').val();
	let url = "/logs/apache_internal/" + serv + "/" + rows;
	$.ajax( {
		url: url,
		data: {
			rows: rows,
			serv: serv,
			grep: grep,
			exgrep: exgrep,
			hour: hour,
			minute: minute,
			hour1: hour1,
			minute1: minute1
		},
		type: "POST",
		success: function( data ) {
			$("#ajax").html(data);
		}
	} );
}
