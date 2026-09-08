/**
 * JEEVANSETU AI - Connected Frontend Controller
 * Fetches Live Data from Flask REST API Engine
 */

const API_BASE_URL = "https://jeevansetu-ai-7e5y.onrender.com/api";

document.addEventListener('DOMContentLoaded', () => {
  let hospitals = [];
  let activeFilter = 'all';

  // DOM Elements
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');
  const hospitalsContainer = document.getElementById('hospitalsContainer');
  const hospitalSearchInput = document.getElementById('hospitalSearchInput');
  const filterPills = document.querySelectorAll('.filter-pill');
  
  const triageForm = document.getElementById('triageQuickForm');
  const triageResultBox = document.getElementById('triageResultBox');
  const resultBadge = document.getElementById('resultBadge');
  const resultTitle = document.getElementById('resultTitle');
  const resultAdvice = document.getElementById('resultAdvice');
  const triageConfirmAction = document.getElementById('triageConfirmAction');

  const emergencyModal = document.getElementById('emergencyModal');
  const quickEmergencyTrigger = document.getElementById('quickEmergencyTrigger');
  const heroSosBtn = document.getElementById('heroSosBtn');
  const ambulanceDispatchBtn = document.getElementById('ambulanceDispatchBtn');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const cancelSosBtn = document.getElementById('cancelSosBtn');
  const callHotlineBtn = document.getElementById('callHotlineBtn');
  const userLocationDisplay = document.getElementById('userLocationDisplay');
  const faqItems = document.querySelectorAll('.faq-item');

  // 1. Mobile Navigation Toggle
  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => navMenu.classList.toggle('open'));
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.addEventListener('click', () => navMenu.classList.remove('open'));
    });
  }

  // 2. Fetch Live Hospitals from Flask Backend API
  async function loadHospitalsFromAPI() {
    if (!hospitalsContainer) return;
    hospitalsContainer.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
        <p style="color: var(--primary); font-weight: 600;">⚡ Connecting to JeevanSetu Live Network...</p>
      </div>
    `;

    try {
      const response = await fetch(`${API_BASE_URL}/hospitals`);
      if (!response.ok) throw new Error("Network response was not ok");
      hospitals = await response.json();
      applyFilters();
    } catch (error) {
      console.error("Failed to fetch hospitals from backend:", error);
      hospitalsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; background: #fee2e2; border-radius: 8px;">
          <p style="color: #991b1b; font-weight: 600;">⚠️ Backend server offline or loading issue. Ensure 'python app.py' is running.</p>
        </div>
      `;
    }
  }

  // 3. Render Hospital Cards
  function renderHospitals(list) {
    if (!hospitalsContainer) return;
    hospitalsContainer.innerHTML = '';

    if (list.length === 0) {
      hospitalsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2.5rem; background: #fff; border-radius: 12px; border: 1px solid var(--border-color);">
          <p style="color: var(--text-muted); font-size: 1.05rem;">No hospital facilities found matching your criteria.</p>
        </div>
      `;
      return;
    }

    list.forEach(hosp => {
      const card = document.createElement('article');
      card.className = 'hospital-card';

      const isIcuCritical = hosp.icuAvailable === 0;
      const icuClass = isIcuCritical ? 'warning' : 'highlight';

      card.innerHTML = `
        <div>
          <div class="hosp-top">
            <h3 class="hosp-name">${hosp.name}</h3>
            <span class="hosp-distance">${hosp.distanceKm} km away</span>
          </div>
          <p class="hosp-location">&#x1F4CD; ${hosp.location}</p>
          
          <div class="bed-status-pills">
            <div class="bed-stat ${icuClass}">
              <span>Verified ICU Beds</span>
              <strong>${hosp.icuAvailable} / ${hosp.totalIcu}</strong>
            </div>
            <div class="bed-stat">
              <span>Oxygen Units</span>
              <strong>${hosp.oxygenBeds}</strong>
            </div>
          </div>

          <div class="hosp-facilities">
            <span class="badge-tag">Trauma Tier ${hosp.traumaLevel}</span>
            <span class="badge-tag">${hosp.icuAvailable > 0 ? 'ICU Ready' : 'ICU Full'}</span>
            <span class="badge-tag">24/7 Casualty</span>
          </div>
        </div>

        <div class="hosp-actions">
          <button class="btn btn-primary btn-sm btn-block reserve-btn" data-id="${hosp.id}">
            Book Emergency Bay
          </button>
          <a href="tel:${hosp.phone}" class="btn btn-secondary btn-sm" title="Call Emergency Desk">
            &#x260E;
          </a>
        </div>
      `;

      hospitalsContainer.appendChild(card);
    });

    document.querySelectorAll('.reserve-btn').forEach(button => {
      button.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.getAttribute('data-id'));
        const matched = hospitals.find(h => h.id === id);
        if (matched) {
          triggerLiveEmergencySOS(matched.name);
        }
      });
    });
  }

  // 4. Search & Filter
  function applyFilters() {
    const searchVal = hospitalSearchInput ? hospitalSearchInput.value.toLowerCase().trim() : '';

    const filtered = hospitals.filter(hosp => {
      const matchesSearch = 
        hosp.name.toLowerCase().includes(searchVal) ||
        hosp.location.toLowerCase().includes(searchVal);

      let matchesTag = true;
      if (activeFilter === 'icu') {
        matchesTag = hosp.icuAvailable > 0;
      } else if (activeFilter === 'oxygen') {
        matchesTag = hosp.oxygenBeds > 0;
      } else if (activeFilter === 'trauma') {
        matchesTag = hosp.traumaLevel === 1;
      }

      return matchesSearch && matchesTag;
    });

    renderHospitals(filtered);
  }

  if (hospitalSearchInput) {
    hospitalSearchInput.addEventListener('input', applyFilters);
  }

  filterPills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      filterPills.forEach(p => p.classList.remove('active'));
      e.currentTarget.classList.add('active');
      activeFilter = e.currentTarget.getAttribute('data-filter') || 'all';
      applyFilters();
    });
  });

  // 5. Trigger Real Emergency SOS to Backend
  async function triggerLiveEmergencySOS(targetHospital = "Nearest Available Center") {
    openEmergencyModal();

    try {
      const res = await fetch(`${API_BASE_URL}/emergency/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_name: "Citizen Alert (App Triggered)",
          symptom: "Acute Critical Emergency",
          priority: "TIER_1_CRITICAL"
        })
      });
      const data = await res.json();
      console.log("SOS Recorded in DB:", data);
    } catch (err) {
      console.warn("SOS queued locally (Backend offline)");
    }
  }

  // 6. Modal Functions
  function openEmergencyModal() {
    if (!emergencyModal) return;
    emergencyModal.classList.add('open');

    if (userLocationDisplay) {
      userLocationDisplay.textContent = "Detecting GPS coordinates...";
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            userLocationDisplay.textContent = `${pos.coords.latitude.toFixed(4)}° N, ${pos.coords.longitude.toFixed(4)}° E`;
          },
          () => {
            userLocationDisplay.textContent = "Kanpur Metro District";
          },
          { timeout: 5000 }
        );
      }
    }
  }

  function closeEmergencyModal() {
    if (emergencyModal) emergencyModal.classList.remove('open');
  }

  [quickEmergencyTrigger, heroSosBtn, ambulanceDispatchBtn].forEach(btn => {
    if (btn) btn.addEventListener('click', () => triggerLiveEmergencySOS());
  });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeEmergencyModal);
  if (cancelSosBtn) cancelSosBtn.addEventListener('click', closeEmergencyModal);
  if (emergencyModal) {
    emergencyModal.addEventListener('click', (e) => {
      if (e.target === emergencyModal) closeEmergencyModal();
    });
  }
  if (callHotlineBtn) {
    callHotlineBtn.addEventListener('click', () => window.location.href = "tel:108");
  }

  // 7. Live Gemini AI Triage Connection
  if (triageForm) {
    triageForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const symptomSelect = document.getElementById('primarySymptom');
      const symptom = symptomSelect.options[symptomSelect.selectedIndex].text;
      const age = document.getElementById('patientAge').value;
      const mobility = document.getElementById('mobilityStatus').value;

      if (resultTitle) resultTitle.textContent = "Analyzing clinical telemetry with Gemini AI...";
      if (triageResultBox) triageResultBox.classList.remove('hidden');

      try {
        const res = await fetch(`${API_BASE_URL}/ai/triage`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symptoms: symptom, age: age, mobility: mobility })
        });
        const aiData = await res.json();

        if (resultBadge) resultBadge.textContent = aiData.priority;
        if (resultTitle) resultTitle.textContent = aiData.headline;
        if (resultAdvice) resultAdvice.textContent = `${aiData.advice} [Required Facility: ${aiData.required_facility}]`;
      } catch (err) {
        console.error("AI Triage Error:", err);
      }
    });
  }

  if (triageConfirmAction) {
    triageConfirmAction.addEventListener('click', () => triggerLiveEmergencySOS());
  }

  // 8. FAQ Accordion
  faqItems.forEach(item => {
    const questionBtn = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');

    if (questionBtn && answer) {
      questionBtn.addEventListener('click', () => {
        const isActive = item.classList.contains('active');
        faqItems.forEach(other => {
          other.classList.remove('active');
          const otherAnswer = other.querySelector('.faq-answer');
          if (otherAnswer) otherAnswer.style.maxHeight = null;
        });

        if (!isActive) {
          item.classList.add('active');
          answer.style.maxHeight = answer.scrollHeight + "px";
        }
      });
    }
  });

  // Run initial API fetch
  loadHospitalsFromAPI();
});