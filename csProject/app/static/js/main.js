$(document).ready(function() {

	$.ajax({
		url: $SCRIPT_ROOT + "/rq/current_jobs",
		method: "GET",
		success: function(data, status, request) {
			$('#current_jobs').text(data + ' job(s) currently running.');
		},
		error: function(jqXHR, textStatus, errorThrown) {
			console.log(jqXHR);
		}
	});

	function flash_alert(message, category, clean) {
		if (typeof(clean) === "undefined") clean = true;
		if(clean) {
			remove_alerts();
		}
		if (typeof(category) === "undefined") category = 'danger';
		var htmlString = '<div class="alert alert-' + category + ' alert-dismissible" role="alert">'
		htmlString += '<button type="button" class="close" data-dismiss="alert" aria-label="Close">'
		htmlString += '<span aria-hidden="true">&times;</span></button>' + message + '</div>'
		$(htmlString).prependTo("#mainContent").hide().slideDown();
	}

	function remove_alerts() {
		$(".alert").slideUp("normal", function() {
			$(this).remove();
		});
	}

	function check_job_status(status_url) {
		$.getJSON(status_url, function(data) {
			switch (data.status) {
				case "unknown":
				flash_alert("Unknown job id", "danger");
				break;
				case "finished":
				flash_alert(data.result, "success");
				break;
				case "failed":
				flash_alert("Job failed: " + data.message, "danger");
				break;
				default:
				setTimeout(function() {
					check_job_status(status_url);
				}, 500);
			}
		});
	}

	// submit form
	$("#submitTaskForm").on('click', function() {
		flash_alert("Archiving... This may take some time. Please come back later.", "info");
		$.ajax({
			url: $SCRIPT_ROOT + "/run_archive_task",
			data: $("#taskForm").serialize(),
			method: "POST",
			dataType: "json",
			success: function(data, status, request) {
				flash_alert(data, 'info');
				var status_url = request.getResponseHeader('Location');
				check_job_status(status_url);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				console.log(jqXHR);
				flash_alert(JSON.parse(jqXHR.responseText));
			}
		});
	});

	// submit form
	$("#submitCSVForm").on('click', function() {
		flash_alert("Archiving... This may take some time. Please come back later.", "info");
		$.ajax({
			url: $SCRIPT_ROOT + "/run_archive_task",
			data: $("#csvForm").serialize(),
			method: "POST",
			dataType: "json",
			success: function(data, status, request) {
				flash_alert(data, 'info');
				var status_url = request.getResponseHeader('Location');
				check_job_status(status_url);
			},
			error: function(jqXHR, textStatus, errorThrown) {
				console.log(jqXHR);
				flash_alert(JSON.parse(jqXHR.responseText));
			}
		});
	});

	// get current job count
	setInterval(function(){
		$.ajax({
			url: $SCRIPT_ROOT + "/rq/current_jobs",
			method: "GET",
			success: function(data, status, request) {
				$('#current_jobs').text(data + ' job(s) currently running.');
			},
			error: function(jqXHR, textStatus, errorThrown) {
				console.log(jqXHR);
			}
		});
	}, 10000);

});