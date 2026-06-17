/* MyWeblog – Public JS */

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});
