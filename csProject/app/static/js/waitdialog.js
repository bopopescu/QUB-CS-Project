/*
** Ref: https://github.com/ehpc/bootstrap-waitingfor.git
*/

var waitingDialog = waitingDialog || (function ($) {
	'use strict';

// Creating modal dialog's DOM
var $dialog = $(
	'<div class="modal fade" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog" aria-hidden="true" style="padding-top:15%; overflow-y:visible;">' +
	'<div class="modal-dialog modal-m">' +
	'<div class="modal-content">' +
	'<div class="modal-header"><h3 style="margin:0;"></h3></div>' +
	'<div class="modal-body">' +
	'<center><img src="/static/images/waiting.gif") }}"></center></div>' +
	'</div>' +
	'</div></div></div>');

return {
	show: function () {
		var message = 'Analysing. Please wait...';
		var settings = $.extend({
			dialogSize: 'm',
		});

		// Configuring dialog
		$dialog.find('.modal-dialog').attr('class', 'modal-dialog').addClass('modal-' + settings.dialogSize);
		$dialog.find('.progress-bar').attr('class', 'progress-bar');
		$dialog.find('h3').text(message);

		$dialog.modal();
	}
};

})(jQuery);