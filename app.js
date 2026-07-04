const SESSION_SIZE = 12;
const state = {
  content: null,
  session: [],
  idx: 0,
  correct: 0,
  streak: 0,
  confidence: [],
  selectedChoice: null,
  selectedChoices: new Set(),
  checked: false,
  lastMode: { review: false },
  user: null,
  progress: loadProgress(),
};

const els = {
  views: document.querySelectorAll('.view'),
  tabs: document.querySelectorAll('.tab'),
  levelLabel: document.getElementById('level-label'),
  metricProgress: document.getElementById('metric-progress'),
  metricCorrect: document.getElementById('metric-correct'),
  metricStreak: document.getElementById('metric-streak'),
  metricConfidence: document.getElementById('metric-confidence'),
  topicProgress: document.getElementById('topic-progress'),
  weakTopics: document.getElementById('weak-topics'),
  attempts: document.getElementById('attempts'),
  topicCards: document.getElementById('topic-cards'),
  catalogLevel: document.getElementById('catalog-level'),
  topicFilter: document.getElementById('topic-filter'),
  typeFilter: document.getElementById('type-filter'),
  quiz: document.getElementById('quiz'),
  result: document.getElementById('result'),
  sessionTitle: document.getElementById('session-title'),
  sessionMeta: document.getElementById('session-meta'),
  progress: document.getElementById('progress'),
  taskKind: document.getElementById('task-kind'),
  question: document.getElementById('question'),
  scenario: document.getElementById('scenario'),
  answers: document.getElementById('answers'),
  openAnswer: document.getElementById('open-answer'),
  confidenceRange: document.getElementById('confidence-range'),
  confidenceValue: document.getElementById('confidence-value'),
  feedback: document.getElementById('feedback'),
  btnStart: document.getElementById('btn-start'),
  btnReview: document.getElementById('btn-review'),
  btnCheck: document.getElementById('btn-check'),
  btnNext: document.getElementById('btn-next'),
  btnSkip: document.getElementById('btn-skip'),
  btnAgain: document.getElementById('btn-again'),
  btnExport: document.getElementById('btn-export'),
  btnRecommended: document.getElementById('btn-start-recommended'),
  resCorrect: document.getElementById('res-correct'),
  resTotal: document.getElementById('res-total'),
  resAcc: document.getElementById('res-acc'),
  resConfidence: document.getElementById('res-confidence'),
  authView: document.getElementById('auth-view'),
  appShell: document.getElementById('app-shell'),
  loginForm: document.getElementById('login-form'),
  loginUsername: document.getElementById('login-username'),
  loginPassword: document.getElementById('login-password'),
  loginError: document.getElementById('login-error'),
  registerForm: document.getElementById('register-form'),
  registerUsername: document.getElementById('register-username'),
  registerPassword: document.getElementById('register-password'),
  registerError: document.getElementById('register-error'),
  btnShowRegister: document.getElementById('btn-show-register'),
  btnShowLogin: document.getElementById('btn-show-login'),
  btnLogout: document.getElementById('btn-logout'),
  adminTab: document.getElementById('admin-tab'),
  adminUsers: document.getElementById('admin-users'),
  adminMessage: document.getElementById('admin-message'),
  btnRefreshUsers: document.getElementById('btn-refresh-users'),
};

function loadProgress() {
  return { answered: {}, wrong: [], attempts: [] };
}

function saveProgress() {
  return fetch('/api/progress', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state.progress),
  });
}

async function init() {
  const me = await fetch('/api/me', { cache: 'no-cache' });
  if (!me.ok) {
    showAuth();
    return;
  }
  state.user = await me.json();
  await loadServerProgress();
  const response = await fetch('/api/content', { cache: 'no-cache' });
  if (!response.ok) {
    showAuth();
    return;
  }
  state.content = await response.json();
  showApp();
  renderFilters();
  renderDashboard();
  renderCatalog();
  if (state.user.role === 'admin') loadAdminUsers();
}

async function loadServerProgress() {
  const response = await fetch('/api/progress', { cache: 'no-cache' });
  state.progress = response.ok ? await response.json() : loadProgress();
}

function showAuth() {
  els.authView.classList.remove('hidden');
  els.appShell.classList.add('hidden');
  els.btnLogout.classList.add('hidden');
  showLoginForm();
}

function showApp() {
  els.authView.classList.add('hidden');
  els.appShell.classList.remove('hidden');
  els.btnLogout.classList.remove('hidden');
  els.adminTab.classList.toggle('hidden', state.user?.role !== 'admin');
}

async function login(event) {
  event.preventDefault();
  els.loginError.textContent = '';
  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: els.loginUsername.value.trim(),
      password: els.loginPassword.value,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    els.loginError.textContent = error.error === 'locked'
      ? 'Слишком много попыток. Вход временно заблокирован.'
      : 'Неверный логин или пароль.';
    return;
  }
  state.user = await response.json();
  await init();
}

function showLoginForm() {
  els.loginForm.classList.remove('hidden');
  els.registerForm.classList.add('hidden');
  els.loginError.textContent = '';
  els.registerError.textContent = '';
}

function showRegisterForm() {
  els.loginForm.classList.add('hidden');
  els.registerForm.classList.remove('hidden');
  els.loginError.textContent = '';
  els.registerError.textContent = '';
}

async function register(event) {
  event.preventDefault();
  els.registerError.textContent = '';
  const response = await fetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: els.registerUsername.value.trim(),
      password: els.registerPassword.value,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const messages = {
      bad_username: 'Логин: 3-32 символа, латиница/цифры/._-',
      weak_password: 'Пароль должен быть минимум 8 символов.',
      user_exists: 'Такой пользователь уже существует.',
    };
    els.registerError.textContent = messages[error.error] || 'Не удалось зарегистрироваться.';
    return;
  }
  state.user = await response.json();
  await init();
}

async function logout() {
  await fetch('/api/logout', { method: 'POST' });
  state.user = null;
  state.content = null;
  state.progress = loadProgress();
  showAuth();
}

function renderFilters() {
  const options = ['<option value="any">Все темы</option>'].concat(
    state.content.topics.map(topic => `<option value="${topic.id}">${topic.title}</option>`)
  );
  els.topicFilter.innerHTML = options.join('');
}

function switchView(view) {
  els.views.forEach(item => item.classList.toggle('active', item.id === view));
  els.tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.view === view));
  if (view === 'admin') loadAdminUsers();
}

function topicStats(topicId) {
  const tasks = state.content.questions.filter(q => q.topic === topicId);
  const answered = tasks.filter(q => state.progress.answered[q.id]);
  const correct = answered.filter(q => state.progress.answered[q.id].correct);
  const total = tasks.length || 1;
  return {
    total: tasks.length,
    answered: answered.length,
    correct: correct.length,
    percent: Math.round((answered.length / total) * 100),
    accuracy: answered.length ? Math.round((correct.length / answered.length) * 100) : 0,
  };
}

function globalStats() {
  const ids = Object.keys(state.progress.answered);
  const correct = ids.filter(id => state.progress.answered[id].correct).length;
  const confidenceValues = ids.map(id => state.progress.answered[id].confidence || 0);
  const avgConfidence = confidenceValues.length
    ? Math.round(confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length)
    : 0;
  const progress = state.content.questions.length
    ? Math.round((ids.length / state.content.questions.length) * 100)
    : 0;
  return { answered: ids.length, correct, avgConfidence, progress };
}

function levelFromProgress(progress) {
  if (progress >= 85) return 'Senior-ready';
  if (progress >= 55) return 'Middle+';
  if (progress >= 25) return 'Middle';
  return 'Junior';
}

function renderDashboard() {
  const stats = globalStats();
  els.metricProgress.textContent = `${stats.progress}%`;
  els.metricCorrect.textContent = String(stats.correct);
  els.metricStreak.textContent = String(state.streak);
  els.metricConfidence.textContent = `${stats.avgConfidence}%`;
  els.levelLabel.textContent = levelFromProgress(stats.progress);

  els.topicProgress.innerHTML = state.content.topics.map(topic => {
    const data = topicStats(topic.id);
    return `
      <button class="topic-row" data-topic="${topic.id}">
        <span>
          <strong>${topic.title}</strong>
          <small>${data.answered}/${data.total} заданий · ${data.accuracy}% accuracy</small>
        </span>
        <i style="--value:${data.percent}%"><b></b></i>
      </button>
    `;
  }).join('');

  const weak = state.content.topics
    .map(topic => ({ topic, stats: topicStats(topic.id) }))
    .filter(item => item.stats.answered > 0 && item.stats.accuracy < 70)
    .sort((a, b) => a.stats.accuracy - b.stats.accuracy)
    .slice(0, 5);
  els.weakTopics.innerHTML = weak.length
    ? weak.map(item => `<button class="mini-item" data-topic="${item.topic.id}">${item.topic.title}<span>${item.stats.accuracy}%</span></button>`).join('')
    : '<p class="muted">Слабые темы появятся после первых ответов.</p>';

  els.attempts.innerHTML = state.progress.attempts.slice(0, 6).map(attempt => `
    <div class="mini-item">
      <span>${attempt.topicTitle} · ${attempt.typeLabel}</span>
      <b>${attempt.correct}/${attempt.total}</b>
    </div>
  `).join('') || '<p class="muted">Попыток пока нет.</p>';

  els.topicProgress.querySelectorAll('[data-topic]').forEach(node => {
    node.addEventListener('click', () => startTopic(node.dataset.topic));
  });
}

function renderCatalog() {
  const level = els.catalogLevel.value;
  const topics = state.content.topics.filter(topic => level === 'any' || topic.level === level);
  els.topicCards.innerHTML = topics.map(topic => {
    const stats = topicStats(topic.id);
    const status = stats.percent === 0 ? 'not started' : stats.percent === 100 ? 'completed' : stats.accuracy < 70 ? 'weak area' : 'in progress';
    return `
      <article class="topic-card">
        <div>
          <span class="badge">${topic.level}</span>
          <h3>${topic.title}</h3>
          <p>${topic.description}</p>
        </div>
        <dl>
          <div><dt>Вопросы</dt><dd>${topic.questionCount}</dd></div>
          <div><dt>Кейсы</dt><dd>${topic.caseCount}</dd></div>
          <div><dt>Прогресс</dt><dd>${stats.percent}%</dd></div>
          <div><dt>Статус</dt><dd>${status}</dd></div>
        </dl>
        <div class="topic-actions">
          <button class="primary" data-action="train" data-topic="${topic.id}">Начать</button>
          <button class="secondary" data-action="review" data-topic="${topic.id}">Ошибки</button>
          <button class="ghost" data-action="interview" data-topic="${topic.id}">Interview</button>
        </div>
      </article>
    `;
  }).join('');

  els.topicCards.querySelectorAll('button').forEach(button => {
    button.addEventListener('click', () => {
      const topic = button.dataset.topic;
      switchView('trainer');
      if (button.dataset.action === 'review') startSession({ topic, review: true });
      else if (button.dataset.action === 'interview') startSession({ topic, type: 'interview' });
      else startSession({ topic });
    });
  });
}

function startTopic(topicId) {
  switchView('trainer');
  startSession({ topic: topicId });
}

function startRecommended() {
  const next = state.content.topics
    .map(topic => ({ topic, stats: topicStats(topic.id) }))
    .sort((a, b) => a.stats.percent - b.stats.percent || a.stats.accuracy - b.stats.accuracy)[0];
  if (next) startTopic(next.topic.id);
}

function startSession(options = {}) {
  const topic = options.topic || els.topicFilter.value;
  const type = options.type || els.typeFilter.value;
  state.lastMode = { topic, type, review: !!options.review };
  els.topicFilter.value = topic || 'any';
  els.typeFilter.value = type || 'any';

  let pool = state.content.questions.slice();
  if (topic && topic !== 'any') pool = pool.filter(q => q.topic === topic);
  if (type && type !== 'any') pool = pool.filter(q => q.type === type);
  if (options.review) {
    const wrong = new Set(state.progress.wrong);
    pool = pool.filter(q => wrong.has(q.id));
  }

  shuffle(pool);
  state.session = pool.slice(0, SESSION_SIZE);
  state.idx = 0;
  state.correct = 0;
  state.streak = 0;
  state.confidence = [];
  els.result.classList.add('hidden');
  els.quiz.classList.remove('hidden');
  renderQuestion();
}

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
}

function renderQuestion() {
  const task = state.session[state.idx];
  if (!task) return endSession();

  state.selectedChoice = null;
  state.selectedChoices = new Set();
  state.checked = false;
  const topic = state.content.topics.find(item => item.id === task.topic);
  els.sessionTitle.textContent = topic ? topic.title : 'Тренировка';
  els.sessionMeta.textContent = `${state.session.length} заданий · ${state.lastMode.review ? 'повтор ошибок' : 'новая сессия'}`;
  els.progress.textContent = `Задание ${state.idx + 1} из ${state.session.length}`;
  const answerMode = Array.isArray(task.answer) ? 'выбери несколько' : 'выбери один';
  els.taskKind.textContent = `${task.typeLabel} · ${task.level} · ${answerMode}`;
  els.question.textContent = task.question;
  els.answers.innerHTML = '';
  els.feedback.innerHTML = '';
  els.btnNext.disabled = true;
  els.btnCheck.disabled = false;
  els.confidenceRange.value = 60;
  els.confidenceValue.textContent = '60%';

  const hasChoices = Array.isArray(task.choices) && task.choices.length > 0;
  els.openAnswer.classList.toggle('hidden', hasChoices);
  els.openAnswer.value = '';
  els.scenario.classList.add('hidden');

  if (hasChoices) {
    task.choices.forEach((choice, index) => {
      const li = document.createElement('li');
      const button = document.createElement('button');
      button.className = 'answer';
      button.textContent = choice;
      button.addEventListener('click', () => selectChoice(index));
      li.appendChild(button);
      els.answers.appendChild(li);
    });
  } else {
    els.scenario.classList.remove('hidden');
    els.scenario.textContent = 'Оцени кейс как на рабочем triage: что проверишь, какой риск, как исправить и что будет evidence.';
  }
}

function selectChoice(index) {
  if (state.checked) return;
  const task = state.session[state.idx];
  const isMultiple = Array.isArray(task.answer);
  if (isMultiple) {
    if (state.selectedChoices.has(index)) state.selectedChoices.delete(index);
    else state.selectedChoices.add(index);
  } else {
    state.selectedChoice = index;
    state.selectedChoices = new Set([index]);
  }
  els.answers.querySelectorAll('.answer').forEach((button, current) => {
    button.classList.toggle('selected', state.selectedChoices.has(current));
  });
}

function checkAnswer() {
  const task = state.session[state.idx];
  const confidence = Number(els.confidenceRange.value);
  state.confidence.push(confidence);
  let correct = false;

  if (Array.isArray(task.choices) && task.choices.length > 0) {
    const answers = Array.isArray(task.answer) ? task.answer : [task.answer];
    const answerSet = new Set(answers);
    correct = answers.length === state.selectedChoices.size
      && answers.every(index => state.selectedChoices.has(index));
    els.answers.querySelectorAll('.answer').forEach((button, index) => {
      button.disabled = true;
      button.classList.toggle('correct', answerSet.has(index));
      button.classList.toggle('wrong', state.selectedChoices.has(index) && !answerSet.has(index));
    });
  } else {
    const score = scoreOpenAnswer(els.openAnswer.value, task);
    correct = score.percent >= 60;
    task._lastOpenScore = score;
  }

  state.checked = true;
  state.correct += correct ? 1 : 0;
  state.streak = correct ? state.streak + 1 : 0;
  rememberAnswer(task, correct, confidence);
  renderFeedback(task, correct);
  els.btnNext.disabled = false;
  els.btnCheck.disabled = true;
  renderDashboard();
}

function rememberAnswer(task, correct, confidence) {
  state.progress.answered[task.id] = {
    correct,
    confidence,
    topic: task.topic,
    type: task.type,
    at: new Date().toISOString(),
  };
  state.progress.wrong = state.progress.wrong.filter(id => id !== task.id);
  if (!correct) state.progress.wrong.push(task.id);
  saveProgress();
}

function renderFeedback(task, correct) {
  const status = correct ? 'Хорошо' : 'Нужно повторить';
  const redFlags = task.redFlags ? `<h4>Red flags</h4><p>${task.redFlags}</p>` : '';
  els.feedback.innerHTML = `
    <div class="${correct ? 'ok' : 'needs-work'}">${status}</div>
    <h4>Разбор</h4>
    <p>${task.explain || task.expectedAnswer || 'Сравни свой ответ с expected answer.'}</p>
    ${redFlags}
  `;
}

function normalizeText(value) {
  return (value || '').toLowerCase().replace(/ё/g, 'е');
}

function scoreOpenAnswer(answer, task) {
  const text = normalizeText(answer);
  const rubric = task.rubric || [];
  if (!rubric.length) {
    return {
      percent: text.trim().length >= 80 ? 70 : 0,
      matched: [],
      missed: ['evidence, impact, root cause, remediation'],
    };
  }

  const matched = rubric.filter(item => {
    const keywords = (item.keywords || [item.label]).map(normalizeText);
    return keywords.some(keyword => keyword && text.includes(keyword));
  });

  return {
    percent: Math.round((matched.length / rubric.length) * 100),
    matched: matched.map(item => item.label),
    missed: rubric.filter(item => !matched.includes(item)).map(item => item.label),
  };
}

function renderFeedback(task, correct) {
  const status = correct ? 'Хорошо' : 'Нужно повторить';
  const answers = Array.isArray(task.answer) ? task.answer : [task.answer];
  const selected = [...state.selectedChoices];
  const missed = Array.isArray(task.choices)
    ? answers.filter(index => !state.selectedChoices.has(index)).map(index => task.choices[index])
    : [];
  const extra = Array.isArray(task.choices)
    ? selected.filter(index => !answers.includes(index)).map(index => task.choices[index])
    : [];
  const choiceDetails = task.choices?.length ? `
    ${missed.length ? `<h4>Пропущено</h4><p>${missed.join('\n')}</p>` : ''}
    ${extra.length ? `<h4>Лишний выбор</h4><p>${extra.join('\n')}</p>` : ''}
  ` : '';
  const openScore = task._lastOpenScore;
  const openDetails = openScore ? `
    <h4>Оценка по rubric: ${openScore.percent}%</h4>
    ${openScore.matched.length ? `<p>Засчитано: ${openScore.matched.join('; ')}</p>` : ''}
    ${openScore.missed.length ? `<p>Не хватило: ${openScore.missed.join('; ')}</p>` : ''}
  ` : '';
  const redFlags = task.redFlags ? `<h4>Red flags</h4><p>${task.redFlags}</p>` : '';
  els.feedback.innerHTML = `
    <div class="${correct ? 'ok' : 'needs-work'}">${status}</div>
    ${choiceDetails}
    ${openDetails}
    <h4>Разбор</h4>
    <p>${task.explain || task.expectedAnswer || 'Сравни свой ответ с expected answer.'}</p>
    ${redFlags}
  `;
}

function nextQuestion() {
  state.idx += 1;
  renderQuestion();
}

function skipQuestion() {
  const task = state.session[state.idx];
  if (task && !state.progress.wrong.includes(task.id)) {
    state.progress.wrong.push(task.id);
    saveProgress();
  }
  nextQuestion();
}

function endSession() {
  els.quiz.classList.add('hidden');
  els.result.classList.remove('hidden');
  const total = state.session.length;
  const accuracy = total ? Math.round((state.correct / total) * 100) : 0;
  const avgConfidence = state.confidence.length
    ? Math.round(state.confidence.reduce((sum, value) => sum + value, 0) / state.confidence.length)
    : 0;
  els.resCorrect.textContent = String(state.correct);
  els.resTotal.textContent = String(total);
  els.resAcc.textContent = `${accuracy}%`;
  els.resConfidence.textContent = `${avgConfidence}%`;

  const topic = state.content.topics.find(item => item.id === state.lastMode.topic);
  const typeLabel = state.lastMode.type === 'any'
    ? 'mixed'
    : (state.session[0]?.typeLabel || state.lastMode.type);
  state.progress.attempts.unshift({
    topicTitle: topic ? topic.title : 'Все темы',
    typeLabel,
    correct: state.correct,
    total,
    confidence: avgConfidence,
    at: new Date().toISOString(),
  });
  state.progress.attempts = state.progress.attempts.slice(0, 12);
  saveProgress();
  renderDashboard();
  renderCatalog();
}

function exportResults() {
  const blob = new Blob([JSON.stringify({
    progress: state.progress,
    exportedAt: new Date().toISOString(),
  }, null, 2)], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'appsec-middle-trainer-progress.json';
  link.click();
  URL.revokeObjectURL(link.href);
}

async function loadAdminUsers() {
  if (state.user?.role !== 'admin') return;
  const response = await fetch('/api/admin/users', { cache: 'no-cache' });
  if (!response.ok) {
    els.adminMessage.textContent = 'Не удалось загрузить пользователей.';
    return;
  }
  const users = await response.json();
  els.adminUsers.innerHTML = users.map(user => `
    <div class="user-row">
      <span>
        <strong>${user.username}</strong>
        <small>${user.role} · answered: ${user.answered} · wrong: ${user.wrong}</small>
      </span>
      <button class="secondary" data-reset-user="${user.username}">Сбросить прогресс</button>
    </div>
  `).join('');
  els.adminUsers.querySelectorAll('[data-reset-user]').forEach(button => {
    button.addEventListener('click', () => resetUserProgress(button.dataset.resetUser));
  });
}

async function resetUserProgress(username) {
  const response = await fetch('/api/admin/reset-progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
  });
  if (!response.ok) {
    els.adminMessage.textContent = `Не удалось сбросить прогресс ${username}.`;
    return;
  }
  els.adminMessage.textContent = `Прогресс ${username} сброшен.`;
  if (username === state.user?.username) {
    state.progress = loadProgress();
    renderDashboard();
    renderCatalog();
  }
  await loadAdminUsers();
}

els.tabs.forEach(tab => tab.addEventListener('click', () => switchView(tab.dataset.view)));
els.catalogLevel.addEventListener('change', renderCatalog);
els.btnStart.addEventListener('click', () => startSession());
els.btnReview.addEventListener('click', () => startSession({ review: true }));
els.btnRecommended.addEventListener('click', startRecommended);
els.btnCheck.addEventListener('click', checkAnswer);
els.btnNext.addEventListener('click', nextQuestion);
els.btnSkip.addEventListener('click', skipQuestion);
els.btnAgain.addEventListener('click', () => startSession(state.lastMode));
els.btnExport.addEventListener('click', exportResults);
els.loginForm.addEventListener('submit', login);
els.registerForm.addEventListener('submit', register);
els.btnShowRegister.addEventListener('click', showRegisterForm);
els.btnShowLogin.addEventListener('click', showLoginForm);
els.btnLogout.addEventListener('click', logout);
els.btnRefreshUsers.addEventListener('click', loadAdminUsers);
els.confidenceRange.addEventListener('input', () => {
  els.confidenceValue.textContent = `${els.confidenceRange.value}%`;
});

init().catch(error => {
  document.body.innerHTML = `<main class="app"><section class="panel"><h1>Не удалось загрузить тренажёр</h1><p>${error.message}</p></section></main>`;
});
