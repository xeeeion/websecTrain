
const size = 15;
let bank = [];
let session = [];
let idx = 0;
let score = 0;
let streak = 0;
let best = Number(localStorage.getItem('best_py') || 0);
let wrongBucket = JSON.parse(localStorage.getItem('wrongBucket_py') || "[]");

const els = {
  quiz: document.getElementById('quiz'),
  question: document.getElementById('question'),
  answers: document.getElementById('answers'),
  feedback: document.getElementById('feedback'),
  progress: document.getElementById('progress'),
  score: document.getElementById('score'),
  streak: document.getElementById('streak'),
  best: document.getElementById('best'),
  btnStart: document.getElementById('btn-start'),
  btnReview: document.getElementById('btn-review'),
  btnNext: document.getElementById('btn-next'),
  btnSkip: document.getElementById('btn-skip'),
  resCorrect: document.getElementById('res-correct'),
  resTotal: document.getElementById('res-total'),
  resAcc: document.getElementById('res-acc'),
  result: document.getElementById('result')
};

els.best.textContent = String(best);

async function fetchBank() {
  const url = new URL('/api/questions', window.location.origin);
  url.searchParams.set('topic', document.getElementById('topic').value);
  url.searchParams.set('difficulty', document.getElementById('difficulty').value);
  const res = await fetch(url.toString(), { cache: 'no-cache' });
  bank = await res.json();
}

function pickSession({review=false}) {
  let pool = bank.slice();
  if (review) {
    const set = new Set(wrongBucket);
    pool = pool.filter(q => set.has(q.id));
  }
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  session = pool.slice(0, size);
  idx = 0; score = 0; streak = 0;
  updateHud();
}

function renderQ() {
  const q = session[idx];
  if (!q) return endSession();
  els.progress.textContent = `Вопрос ${idx+1} из ${session.length} · [${q.topic} · ${q.difficulty}]`;
  els.question.textContent = q.q;
  els.answers.innerHTML = '';
  els.feedback.textContent = '';
  els.btnNext.disabled = true;

  q.choices.forEach((choice, i) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.className = 'answer';
    btn.textContent = choice;
    btn.addEventListener('click', () => onAnswer(i));
    li.appendChild(btn);
    els.answers.appendChild(li);
  });
}

function onAnswer(i) {
  const q = session[idx];
  const nodes = els.answers.querySelectorAll('.answer');
  nodes.forEach((n, j) => {
    if (j === q.a) n.classList.add('correct');
    if (j === i && i !== q.a) n.classList.add('wrong');
    n.disabled = true;
  });

  const ok = i === q.a;
  if (ok) {
    score += 10; streak += 1;
    if (streak % 5 === 0) score += 5;
    els.feedback.textContent = `Верно. ${q.explain}`;
    wrongBucket = wrongBucket.filter(id => id !== q.id);
  } else {
    streak = 0;
    els.feedback.textContent = `Неверно. ${q.explain}`;
    if (!wrongBucket.includes(q.id)) wrongBucket.push(q.id);
  }
  localStorage.setItem('wrongBucket_py', JSON.stringify(wrongBucket));
  els.btnNext.disabled = false;
  updateHud();
}

function updateHud() {
  document.getElementById('score').textContent = String(score);
  document.getElementById('streak').textContent = String(streak);
  if (score > best) {
    best = score;
    localStorage.setItem('best_py', String(best));
  }
  document.getElementById('best').textContent = String(best);
}

function nextQ() { idx += 1; renderQ(); }
function skipQ() {
  els.feedback.textContent = 'Пропущено.';
  els.btnNext.disabled = false;
  if (session[idx]) {
    wrongBucket.push(session[idx].id);
    localStorage.setItem('wrongBucket_py', JSON.stringify(wrongBucket));
  }
}
function endSession() {
  els.quiz.classList.add('hidden');
  document.getElementById('result').classList.remove('hidden');
  document.getElementById('res-correct').textContent = String(Math.round(score / 10));
  document.getElementById('res-total').textContent = String(session.length);
  const acc = Math.round((score / (session.length * 10)) * 100);
  document.getElementById('res-acc').textContent = `${acc}%`;
}
function exportResults() {
  const blob = new Blob([JSON.stringify({
    score, streak, best, wrongBucket, at: new Date().toISOString()
  }, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'appsec-dojo-python-results.json';
  a.click();
  URL.revokeObjectURL(a.href);
}

document.getElementById('btn-start').addEventListener('click', async () => {
  document.getElementById('result').classList.add('hidden'); 
  document.getElementById('quiz').classList.remove('hidden');
  await fetchBank(); pickSession({}); renderQ();
});
document.getElementById('btn-review').addEventListener('click', async () => {
  document.getElementById('result').classList.add('hidden'); 
  document.getElementById('quiz').classList.remove('hidden');
  await fetchBank(); pickSession({review:true}); renderQ();
});
document.getElementById('btn-next').addEventListener('click', nextQ);
document.getElementById('btn-skip').addEventListener('click', skipQ);
document.getElementById('btn-again')?.addEventListener('click', async () => {
  document.getElementById('result').classList.add('hidden'); 
  document.getElementById('quiz').classList.remove('hidden');
  await fetchBank(); pickSession({}); renderQ();
});
document.getElementById('btn-export')?.addEventListener('click', exportResults);
