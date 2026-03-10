/**
 * Geolocation capture for dynamic forms.
 * Captures browser location and reverse geocodes via Nominatim.
 */
(function() {
    'use strict';

    function initGeolocation() {
        document.querySelectorAll('.geolocation-capture-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var targetId = btn.getAttribute('data-target');
                var input = document.getElementById(targetId);
                var display = document.getElementById(targetId + '_display');

                if (!navigator.geolocation) {
                    alert('Geolocation is not supported by your browser.');
                    return;
                }

                btn.disabled = true;
                btn.textContent = 'Capturing...';

                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        var lat = position.coords.latitude.toFixed(6);
                        var lng = position.coords.longitude.toFixed(6);
                        var value = lat + ',' + lng;
                        input.value = value;

                        if (display) {
                            display.textContent = value + ' (looking up address...)';
                        }

                        // Reverse geocode via Nominatim
                        fetch('https://nominatim.openstreetmap.org/reverse?format=json&lat=' + lat + '&lon=' + lng)
                            .then(function(resp) { return resp.json(); })
                            .then(function(data) {
                                if (data.display_name && display) {
                                    display.textContent = value + ' — ' + data.display_name;
                                }
                            })
                            .catch(function() {
                                if (display) {
                                    display.textContent = value;
                                }
                            });

                        btn.disabled = false;
                        btn.innerHTML = '<span class="geolocation-icon">&#128205;</span> Recapture';
                    },
                    function(error) {
                        alert('Unable to capture location: ' + error.message);
                        btn.disabled = false;
                        btn.innerHTML = '<span class="geolocation-icon">&#128205;</span> Capture Location';
                    },
                    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                );
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGeolocation);
    } else {
        initGeolocation();
    }
})();
