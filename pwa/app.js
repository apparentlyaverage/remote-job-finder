const APPLICATIONS_KEY = "remote-job-finder:applications"; // { [jobId]: { appliedAt, followedUp } }
const EMAILS_KEY = "remote-job-finder:companyEmails"; // { [jobId]: "email" }
const NAME_KEY = "remote-job-finder:yourName";

const FOLLOWUP_DELAY_MS = 24 * 60 * 60 * 1000; // 24 hours

function safeGetJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function safeSetJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage unavailable (private window, etc.) — state just won't
    // persist across reloads. Not fatal, nothing else depends on it.
  }
}

let applications = safeGetJSON(APPLICATIONS_KEY, {});
let companyEmails = safeGetJSON(EMAILS_KEY, {});
let allJobs = [];

function saveApplications() {
  safeSetJSON(APPLICATIONS_KEY, applications);
}

function saveEmails() {
  safeSetJSON(EMAILS_KEY, companyEmails);
}

function getYourName() {
  try {
    return localStorage.getItem(NAME_KEY) || "";
  } catch {
    return "";
  }
}

function setYourName(name) {
  try {
    localStorage.setItem(NAME_KEY, name);
  } catch {
    // ignore
  }
}

function fitClass(fit) {
  if (fit === null || fit === undefined) return "fit-none";
  return `fit-${fit}`;
}

function fitLabel(fit) {
  if (fit === null || fit === undefined) return "Unscored";
  return `Fit ${fit}/5`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function hoursAgo(isoString) {
  const then = new Date(isoString).getTime();
  if (Number.isNaN(then)) return null;
  return (Date.now() - then) / (1000 * 60 * 60);
}

function isFollowUpDue(jobId) {
  const app = applications[jobId];
  if (!app || app.followedUp) return false;
  const hrs = hoursAgo(app.appliedAt);
  return hrs !== null && hrs >= 24;
}

function buildFollowUpEmail(job) {
  const name = getYourName() || "[Your Name]";
  const app = applications[job.id];
  const appliedDate = app ? new Date(app.appliedAt).toLocaleDateString() : "recently";
  const subject = `Following up on my application — ${job.title}`;
  const bodyLines = [
    `Hi ${job.company} team,`,
    "",
    `I wanted to follow up on my application for the ${job.title} role, submitted on ${appliedDate}. ` +
      `I'm still very interested in the opportunity and wanted to check if there's any additional ` +
      `information I can provide to help move my application forward.`,
  ];
  if (job.resume_angle) {
    bodyLines.push("", job.resume_angle);
  }
  bodyLines.push(
    "",
    "Thank you for your time and consideration — I look forward to hearing from you.",
    "",
    "Best regards,",
    name
  );
  return { subject, body: bodyLines.join("\n") };
}

function renderJobs() {
  const sortMode = document.getElementById("sortSelect").value;
  const filterMode = document.getElementById("filterSelect").value;
  const search = document.getElementById("searchBox").value.trim().toLowerCase();

  let jobs = allJobs.slice();

  if (filterMode === "unapplied") {
    jobs = jobs.filter((j) => !applications[j.id]);
  } else if (filterMode === "applied") {
    jobs = jobs.filter((j) => !!applications[j.id]);
  } else if (filterMode === "followup") {
    jobs = jobs.filter((j) => isFollowUpDue(j.id));
  }

  if (search) {
    jobs = jobs.filter(
      (j) =>
        j.title.toLowerCase().includes(search) ||
        j.company.toLowerCase().includes(search)
    );
  }

  if (sortMode === "fit") {
    jobs.sort((a, b) => (b.fit ?? -1) - (a.fit ?? -1));
  } else {
    jobs.sort((a, b) => (b.date_found || "").localeCompare(a.date_found || ""));
  }

  const listEl = document.getElementById("jobList");
  const followUpCount = allJobs.filter((j) => isFollowUpDue(j.id)).length;
  document.getElementById("count").textContent =
    `${jobs.length} shown of ${allJobs.length} total` +
    (followUpCount > 0 ? ` · ${followUpCount} follow-up${followUpCount === 1 ? "" : "s"} due` : "");

  if (jobs.length === 0) {
    listEl.innerHTML = `<div class="empty-state">No jobs match this view.</div>`;
    return;
  }

  listEl.innerHTML = jobs
    .map((job) => {
      const app = applications[job.id];
      const isApplied = !!app;
      const followUpDue = isFollowUpDue(job.id);
      const email = companyEmails[job.id] || "";

      let appliedMeta = "";
      if (isApplied) {
        const hrs = hoursAgo(app.appliedAt);
        const hrsLabel = hrs === null ? "" : hrs < 1 ? "just now" : `${Math.floor(hrs)}h ago`;
        appliedMeta = `<p class="job-meta">Applied ${escapeHtml(hrsLabel)}${app.followedUp ? " · followed up ✓" : ""}</p>`;
      }

      const followUp = buildFollowUpEmail(job);

      return `
        <div class="job-card ${isApplied && !followUpDue ? "applied" : ""} ${followUpDue ? "followup-due" : ""}" data-id="${escapeHtml(job.id)}">
          <div class="job-card-top">
            <div>
              <p class="job-title">${escapeHtml(job.title)} — ${escapeHtml(job.company)}</p>
              <p class="job-meta">${escapeHtml(job.source)} · ${escapeHtml(job.location)} · found ${escapeHtml(job.date_found)}</p>
              ${appliedMeta}
            </div>
            <span class="fit-badge ${fitClass(job.fit)}">${fitLabel(job.fit)}</span>
          </div>
          ${job.resume_angle ? `<p class="resume-angle"><strong>Lead with:</strong> ${escapeHtml(job.resume_angle)}</p>` : ""}
          <p class="blurb">${escapeHtml(job.blurb)}</p>
          <div class="job-actions">
            <a class="btn btn-apply" href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">Apply →</a>
            <button class="btn btn-copy" data-action="copy">Copy blurb</button>
            <button class="btn btn-applied-toggle ${isApplied ? "is-applied" : ""}" data-action="toggle-applied">
              ${isApplied ? "✓ Applied" : "Mark as applied"}
            </button>
          </div>
          ${
            followUpDue
              ? `
            <div class="followup-panel">
              <p class="followup-label">⏰ Follow-up due — it's been 24h+ since you applied</p>
              <input
                type="email"
                class="followup-email-input"
                placeholder="Company contact email (optional — leave blank to just copy the text)"
                value="${escapeHtml(email)}"
                data-action-input="email"
              />
              <p class="followup-subject"><strong>Subject:</strong> ${escapeHtml(followUp.subject)}</p>
              <textarea class="followup-body" readonly>${escapeHtml(followUp.body)}</textarea>
              <div class="job-actions">
                <button class="btn btn-copy" data-action="copy-followup">Copy email text</button>
                <a class="btn btn-apply" data-action="mailto-followup" href="mailto:${escapeHtml(email)}?subject=${encodeURIComponent(followUp.subject)}&body=${encodeURIComponent(followUp.body)}">
                  Open in mail app →
                </a>
                <button class="btn btn-applied-toggle" data-action="mark-followed-up">Mark as followed up</button>
              </div>
            </div>
          `
              : ""
          }
        </div>
      `;
    })
    .join("");
}

function attachListEventDelegation() {
  const listEl = document.getElementById("jobList");

  listEl.addEventListener("input", (e) => {
    if (e.target.dataset.actionInput === "email") {
      const card = e.target.closest(".job-card");
      const id = card.dataset.id;
      companyEmails[id] = e.target.value.trim();
      saveEmails();
      // Update the mailto link live without a full re-render (keeps focus in the input).
      const mailtoLink = card.querySelector('[data-action="mailto-followup"]');
      if (mailtoLink) {
        const job = allJobs.find((j) => j.id === id);
        const followUp = buildFollowUpEmail(job);
        mailtoLink.href = `mailto:${encodeURIComponent(companyEmails[id])}?subject=${encodeURIComponent(followUp.subject)}&body=${encodeURIComponent(followUp.body)}`;
      }
    }
  });

  listEl.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const card = btn.closest(".job-card");
    const id = card.dataset.id;
    const job = allJobs.find((j) => j.id === id);
    if (!job) return;

    if (btn.dataset.action === "copy") {
      try {
        await navigator.clipboard.writeText(job.blurb);
        flashButton(btn, "Copied!");
      } catch {
        alert("Couldn't copy automatically — select the text manually.");
      }
    }

    if (btn.dataset.action === "copy-followup") {
      const followUp = buildFollowUpEmail(job);
      try {
        await navigator.clipboard.writeText(`Subject: ${followUp.subject}\n\n${followUp.body}`);
        flashButton(btn, "Copied!");
      } catch {
        alert("Couldn't copy automatically — select the text manually.");
      }
    }

    if (btn.dataset.action === "toggle-applied") {
      if (applications[id]) {
        delete applications[id];
      } else {
        applications[id] = { appliedAt: new Date().toISOString(), followedUp: false };
      }
      saveApplications();
      renderJobs();
    }

    if (btn.dataset.action === "mark-followed-up") {
      if (applications[id]) {
        applications[id].followedUp = true;
        saveApplications();
        renderJobs();
      }
    }
  });
}

function flashButton(btn, tempText) {
  const original = btn.textContent;
  btn.textContent = tempText;
  setTimeout(() => (btn.textContent = original), 1200);
}

function setupNamePrompt() {
  const existing = getYourName();
  if (existing) return;
  // Only asked once, lazily — not on every load. A follow-up email's
  // sign-off needs a name; skip this and it just falls back to
  // "[Your Name]" as a placeholder you fill in before sending.
}

async function loadJobs() {
  const subtitle = document.getElementById("subtitle");
  try {
    const res = await fetch("/api/jobs", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allJobs = await res.json();
    subtitle.textContent = `${allJobs.length} match(es) tracked · never auto-applies or auto-emails, you send everything yourself`;
    renderJobs();
  } catch (err) {
    subtitle.textContent = "Couldn't load job data — is serve_pwa.py running?";
    document.getElementById("jobList").innerHTML = `<div class="empty-state">
      Failed to fetch /api/jobs (${escapeHtml(String(err))}).<br />
      Make sure you started this page via <code>python serve_pwa.py</code>, not by opening the file directly.
    </div>`;
  }
}

document.getElementById("sortSelect").addEventListener("change", renderJobs);
document.getElementById("filterSelect").addEventListener("change", renderJobs);
document.getElementById("searchBox").addEventListener("input", renderJobs);

const nameInput = document.getElementById("yourNameInput");
if (nameInput) {
  nameInput.value = getYourName();
  nameInput.addEventListener("change", () => {
    setYourName(nameInput.value.trim());
    renderJobs(); // refresh any visible follow-up drafts with the new sign-off
  });
}

attachListEventDelegation();
setupNamePrompt();
loadJobs();

// Re-check follow-up due status periodically so it updates without a reload.
setInterval(renderJobs, 60 * 1000);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {
      // Non-fatal — the app still works without offline caching.
    });
  });
}
