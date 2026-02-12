
// Initialize Map
const map = L.map('map').setView([39.8283, -98.5795], 5); // Centers on USA

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// Layer Groups
let routeLayer = L.layerGroup().addTo(map);
let markersLayer = L.layerGroup().addTo(map);

// DOM Elements
const form = document.getElementById('route-form');
const startInput = document.getElementById('start');
const endInput = document.getElementById('end');
const optimizeBtn = document.getElementById('optimize-btn');
const loader = document.querySelector('.loader');
const btnText = document.querySelector('.btn-text');
const resultsPanel = document.getElementById('results-panel');
const errorMessage = document.getElementById('error-message');
const totalCostEl = document.getElementById('total-cost');
const totalDistEl = document.getElementById('total-dist');
const fuelUsedEl = document.getElementById('fuel-used'); // Added
const stopsList = document.getElementById('stops-list');

// Icons
const startIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const endIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const fuelIcon = L.divIcon({
    className: 'fuel-marker',
    html: '<div style="background-color: #388bfd; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

// Event Listeners
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Reset UI
    errorMessage.classList.add('hidden');
    resultsPanel.classList.add('hidden');
    routeLayer.clearLayers();
    markersLayer.clearLayers();

    // Loading State
    optimizeBtn.disabled = true;
    loader.classList.remove('hidden');
    btnText.textContent = 'Optimizing...';

    const start = startInput.value;
    const end = endInput.value;

    try {
        const response = await fetch('/api/v1/route/optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_location: start,
                end_location: end
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || errData.detail || 'Failed to optimize route');
        }

        const data = await response.json();

        renderRoute(data);

        try {
            updateStats(data);
        } catch (e) {
            console.error("Error updating stats:", e);
        }

        resultsPanel.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        errorMessage.textContent = error.message;
        errorMessage.classList.remove('hidden');
    } finally {
        optimizeBtn.disabled = false;
        loader.classList.add('hidden');
        btnText.textContent = 'Optimize Route';
    }
});

function renderRoute(data) {
    if (data.route && data.route.geometry && data.route.geometry.coordinates) {
        // Decode geometry if needed (OSRM might return polyline string or geojson)
        // Our backend returns GeoJSON coordinates directly from OSRM
        // Note: OSRM uses [lon, lat], Leaflet expects [lat, lon] usually

        const coords = data.route.geometry.coordinates.map(c => [c[1], c[0]]); // Swap to lat,lon

        const polyline = L.polyline(coords, {
            color: '#388bfd',
            weight: 5,
            opacity: 0.8
        }).addTo(routeLayer);

        try {
            map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
        } catch (e) { console.warn("Could not fit bounds", e); }

        // Start Marker
        if (coords.length > 0) {
            L.marker(coords[0], { icon: startIcon })
                .bindPopup(`<b>Start</b><br>${data.route.start || 'Start'}`)
                .addTo(markersLayer);

            // End Marker
            L.marker(coords[coords.length - 1], { icon: endIcon })
                .bindPopup(`<b>End</b><br>${data.route.end || 'End'}`)
                .addTo(markersLayer);
        }
    }

    // Fuel Stops
    if (data.stops && data.stops.length > 0) {
        stopsList.innerHTML = '';

        data.stops.forEach((stop, index) => {
            // Render on Map
            L.marker([stop.lat, stop.lon], { icon: fuelIcon })
                .bindPopup(`<b>${stop.station}</b><br>Price: ${stop.price}<br>City: ${stop.city}, ${stop.state}`)
                .addTo(markersLayer);

            // Add to List
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="station-info">
                    <div class="station-name">Stop #${index + 1}: ${stop.city}, ${stop.state}</div>
                    <div style="font-size: 0.8em; color: #8b949e;">${stop.station}</div>
                </div>
                <div class="station-price">${stop.price}</div>
            `;
            stopsList.appendChild(li);
        });
    } else {
        stopsList.innerHTML = '<li><span style="color: #8b949e; font-size: 0.9em;">No fuel stops needed.</span></li>';
    }
}

function updateStats(data) {
    // Format currency
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    });

    if (totalCostEl) totalCostEl.textContent = formatter.format(data.total_cost || 0);
    if (totalDistEl && data.route) totalDistEl.textContent = `${(data.route.distance_miles || 0).toFixed(1)} mi`;

    // Check if fuel_consumed_gallons exists
    if (fuelUsedEl) {
        if (data.fuel_consumed_gallons !== undefined) {
            fuelUsedEl.textContent = `${data.fuel_consumed_gallons.toFixed(1)} gal`;
            if (fuelUsedEl.parentElement) fuelUsedEl.parentElement.classList.remove('hidden');
        } else {
            if (fuelUsedEl.parentElement) fuelUsedEl.parentElement.classList.add('hidden');
        }
    }
}
// ============================================
// NEARBY STATIONS FEATURE
// ============================================

const nearbyLocationInput = document.getElementById('nearby-location');
const nearbyRadiusInput = document.getElementById('nearby-radius');
const searchNearbyBtn = document.getElementById('search-nearby-btn');
const nearbyLoader = document.querySelector('.nearby-loader');
const nearbyResults = document.getElementById('nearby-results');
const nearbyList = document.getElementById('nearby-list');
const nearbyCount = document.getElementById('nearby-count');

// Layer group for nearby markers
let nearbyMarkersLayer = L.layerGroup().addTo(map);

// Nearby station icon (different color)
const nearbyIcon = L.divIcon({
    className: 'nearby-marker',
    html: '<div style="background-color: #58a6ff; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

// Search nearby button click handler
searchNearbyBtn.addEventListener('click', async () => {
    const location = nearbyLocationInput.value.trim();
    const radius = parseFloat(nearbyRadiusInput.value) || 10;

    if (!location) {
        alert('Please enter a location');
        return;
    }

    // Loading state
    searchNearbyBtn.disabled = true;
    nearbyLoader.classList.remove('hidden');
    nearbyResults.classList.add('hidden');
    nearbyMarkersLayer.clearLayers();

    try {
        // 1. Geocode location
        const geocodeUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location)}&format=json&limit=1&countrycodes=us`;
        const geocodeResponse = await fetch(geocodeUrl, {
            headers: {
                'User-Agent': 'fuel-route-optimizer'
            }
        });

        if (!geocodeResponse.ok) {
            throw new Error('Could not find location');
        }

        const geocodeData = await geocodeResponse.json();

        if (!geocodeData || geocodeData.length === 0) {
            throw new Error('Location not found');
        }

        const lat = parseFloat(geocodeData[0].lat);
        const lon = parseFloat(geocodeData[0].lon);

        // 2. Fetch nearby stations
        const stationsResponse = await fetch(
            `/api/v1/stations/near?lat=${lat}&lon=${lon}&radius=${radius}`
        );

        if (!stationsResponse.ok) {
            const errData = await stationsResponse.json();
            throw new Error(errData.error || 'Failed to fetch stations');
        }

        const stationsData = await stationsResponse.json();
        const stations = stationsData.stations || [];

        // 3. Display results
        displayNearbyStations(stations, lat, lon);

    } catch (error) {
        console.error('Nearby search error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        searchNearbyBtn.disabled = false;
        nearbyLoader.classList.add('hidden');
    }
});

function displayNearbyStations(stations, centerLat, centerLon) {
    // Clear previous markers
    nearbyMarkersLayer.clearLayers();

    if (stations.length === 0) {
        nearbyList.innerHTML = '<li style="color: #8b949e; font-size: 0.9em;">No stations found in this area.</li>';
        nearbyResults.classList.remove('hidden');
        nearbyCount.textContent = '0';
        return;
    }

    // Update count
    nearbyCount.textContent = stations.length;

    // Sort by price (cheapest first)
    stations.sort((a, b) => a.price - b.price);

    // Clear list
    nearbyList.innerHTML = '';

    // Add center marker
    const centerMarker = L.marker([centerLat, centerLon], { icon: startIcon })
        .bindPopup('<b>Search Location</b>')
        .addTo(nearbyMarkersLayer);

    // Add station markers and list items
    stations.forEach((station, index) => {
        // Add marker to map
        const marker = L.marker([station.lat, station.lon], { icon: nearbyIcon })
            .bindPopup(`
                <b>${station.station}</b><br>
                Price: $${station.price.toFixed(3)}/gal<br>
                ${station.city}, ${station.state}<br>
                <small>${station.address}</small>
            `)
            .addTo(nearbyMarkersLayer);

        // Add to list
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="station-info">
                <div class="station-name">#${index + 1}: ${station.station}</div>
                <div style="font-size: 0.8em; color: #8b949e;">${station.city}, ${station.state}</div>
            </div>
            <div class="station-price">$${station.price.toFixed(3)}/gal</div>
        `;

        // Click to focus on map
        li.style.cursor = 'pointer';
        li.addEventListener('click', () => {
            map.setView([station.lat, station.lon], 13);
            marker.openPopup();
        });

        nearbyList.appendChild(li);
    });

    // Show results panel
    nearbyResults.classList.remove('hidden');

    // Fit map to show all markers
    const allLatLngs = [[centerLat, centerLon], ...stations.map(s => [s.lat, s.lon])];
    const bounds = L.latLngBounds(allLatLngs);
    map.fitBounds(bounds, { padding: [50, 50] });
}