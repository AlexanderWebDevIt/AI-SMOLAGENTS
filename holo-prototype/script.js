(function () {
  var canvas = document.getElementById('sparks');
  var ctx = canvas.getContext('2d');
  var hub = document.querySelector('.hub');
  var stage = document.querySelector('.holo-stage');
  var chat = document.getElementById('chat');
  var input = document.getElementById('input');

  var W = 0, H = 0;
  var hubX = 0, hubY = 0, targetX = 0, targetY = 0;
  var particles = [];
  var sparksOn = true;
  var flatMode = false;
  var COUNT = 46;

  function measure() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var hr = hub.getBoundingClientRect();
    var sr = stage.getBoundingClientRect();
    hubX = hr.left + hr.width / 2;
    hubY = hr.top + 10;
    targetX = sr.left + sr.width * 0.40;
    targetY = sr.bottom - 24;
  }

  function spawn() {
    return {
      sx: hubX + (Math.random() - 0.5) * 30,
      sy: hubY,
      tx: targetX + (Math.random() - 0.5) * 150,
      ty: targetY + (Math.random() - 0.5) * 50,
      t: 0,
      speed: 0.0020 + Math.random() * 0.0038,
      phase: Math.random() * Math.PI * 2,
      freq: 1.5 + Math.random() * 2.6,
      amp: 7 + Math.random() * 24,
      size: 0.7 + Math.random() * 1.9,
      life: 0.5 + Math.random() * 0.5
    };
  }

  function reset() {
    particles = [];
    for (var i = 0; i < COUNT; i++) {
      var p = spawn();
      p.t = Math.random();
      particles.push(p);
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    if (!sparksOn || flatMode) {
      requestAnimationFrame(draw);
      return;
    }

    ctx.shadowBlur = 8;
    ctx.shadowColor = 'rgba(240, 180, 41, 0.95)';

    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      p.t += p.speed;
      if (p.t >= 1) {
        particles[i] = spawn();
        continue;
      }

      var e = p.t * p.t * (3 - 2 * p.t);
      var wobble = Math.sin(p.t * p.freq * Math.PI * 2 + p.phase) * p.amp * (1 - p.t);
      var x = p.sx + (p.tx - p.sx) * e + wobble;
      var y = p.sy + (p.ty - p.sy) * e;
      var alpha = Math.sin(p.t * Math.PI) * p.life;

      ctx.globalAlpha = alpha;
      ctx.fillStyle = '#ffd47a';
      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    requestAnimationFrame(draw);
  }

  function now() {
    var d = new Date();
    return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
  }

  function addMsg(text, who) {
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + who;
    var body = document.createElement('div');
    body.className = 'msg-body';
    body.textContent = text;
    var foot = document.createElement('div');
    foot.className = 'msg-foot';
    foot.textContent = now();
    body.appendChild(foot);
    wrap.appendChild(body);
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
  }

  function send() {
    var text = input.value.trim();
    if (!text) return;
    addMsg(text, 'user');
    input.value = '';
    input.style.height = 'auto';
    setTimeout(function () {
      addMsg('Прототип: модель не подключена. Здесь будет ответ твоего агента.', 'bot');
    }, 750);
  }

  document.getElementById('send').addEventListener('click', send);

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

  var btnHolo = document.getElementById('btnHolo');
  var btnFlat = document.getElementById('btnFlat');

  btnHolo.addEventListener('click', function () {
    flatMode = false;
    document.body.classList.remove('mode-flat');
    btnHolo.classList.add('active');
    btnFlat.classList.remove('active');
    setTimeout(measure, 500);
  });

  btnFlat.addEventListener('click', function () {
    flatMode = true;
    document.body.classList.add('mode-flat');
    btnFlat.classList.add('active');
    btnHolo.classList.remove('active');
  });

  document.getElementById('chkSparks').addEventListener('change', function () {
    sparksOn = this.checked;
  });

  document.getElementById('chkScan').addEventListener('change', function () {
    document.body.classList.toggle('no-scan', !this.checked);
  });

  document.getElementById('chkFloat').addEventListener('change', function () {
    document.body.classList.toggle('animate-float', this.checked);
  });

  document.getElementById('rngTilt').addEventListener('input', function () {
    document.documentElement.style.setProperty('--tilt', this.value + 'deg');
  });

  var rngX = document.getElementById('rngX');
  var rngY = document.getElementById('rngY');
  function applyShift() {
    document.documentElement.style.setProperty('--stage-x', rngX.value + 'px');
    document.documentElement.style.setProperty('--stage-y', rngY.value + 'px');
  }
  rngX.addEventListener('input', applyShift);
  rngY.addEventListener('input', applyShift);
  applyShift();

  document.body.classList.add('animate-float');

  window.addEventListener('resize', function () {
    measure();
    reset();
  });

  measure();
  reset();
  draw();
  chat.scrollTop = chat.scrollHeight;
})();
