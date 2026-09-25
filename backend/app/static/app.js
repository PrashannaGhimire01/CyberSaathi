const resultBox = document.getElementById("result");
const languageSelect = document.getElementById("language");

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.remove("hidden");
    resultBox.className = "hidden";
  });
});

async function callApi(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, language: languageSelect.value }),
  });
  if (!response.ok) throw new Error("Request failed: " + response.status);
  return response.json();
}

function addElement(parent, tag, text, className) {
  const el = document.createElement(tag);
  if (text) el.textContent = text;
  if (className) el.className = className;
  parent.appendChild(el);
  return el;
}

function addList(parent, items, ordered) {
  const list = addElement(parent, ordered ? "ol" : "ul");
  items.forEach((item) => addElement(list, "li", item));
}

function showAnalysis(data) {
  const e = data.explanation;
  resultBox.replaceChildren();
  resultBox.className = "result " + data.risk.toLowerCase();
  addElement(resultBox, "h2", e.headline);
  addElement(resultBox, "p", data.risk + " · " + data.score + "/100", "score");
  if (e.reasons.length) {
    addElement(resultBox, "h3", "Why? / किन?");
    addList(resultBox, e.reasons, false);
  }
  addElement(resultBox, "h3", "What to do / के गर्ने?");
  addList(resultBox, e.actions, false);
  addElement(resultBox, "p", e.disclaimer, "disclaimer");
}

function showSteps(steps) {
  resultBox.replaceChildren();
  resultBox.className = "result emergency";
  addElement(resultBox, "h2", "Do these steps now / अहिले यी कदमहरू चाल्नुहोस्");
  addList(resultBox, steps, true);
}

function showError(error) {
  resultBox.replaceChildren();
  resultBox.className = "result error";
  addElement(resultBox, "p", "Something went wrong. Please try again. / केही गडबड भयो। फेरि प्रयास गर्नुहोस्।");
  console.error(error);
}

async function run(action) {
  try {
    await action();
  } catch (error) {
    showError(error);
  }
}

document.getElementById("message-btn").addEventListener("click", () => run(async () => {
  const message = document.getElementById("message-input").value.trim();
  if (message) showAnalysis(await callApi("/analyze/message", { message }));
}));

document.getElementById("url-btn").addEventListener("click", () => run(async () => {
  const url = document.getElementById("url-input").value.trim();
  if (url) showAnalysis(await callApi("/analyze/url", { url }));
}));

document.getElementById("emergency-btn").addEventListener("click", () => run(async () => {
  const boxes = document.querySelectorAll("#emergency input:checked");
  const shared = Array.from(boxes).map((box) => box.value);
  showSteps((await callApi("/emergency", { shared })).steps);
}));