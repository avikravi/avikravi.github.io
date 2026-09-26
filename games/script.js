// Games hub: starfield, the Thermostat Panic dial animation, and arrow-key game select.
(function () {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // --- Starfield -------------------------------------------------------
    var canvas = document.querySelector('.arcade-stars');
    if (canvas && canvas.getContext) {
        var ctx = canvas.getContext('2d');
        var stars = [];
        function resize() {
            var r = canvas.parentElement.getBoundingClientRect();
            var dpr = window.devicePixelRatio || 1;
            canvas.width = r.width * dpr;
            canvas.height = r.height * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            stars = [];
            var count = Math.round(r.width * r.height / 6000);
            for (var i = 0; i < count; i++) {
                stars.push({ x: Math.random() * r.width, y: Math.random() * r.height * 0.6, s: Math.random() < 0.15 ? 2 : 1, p: Math.random() * Math.PI * 2 });
            }
        }
        function draw(t) {
            var w = canvas.width, h = canvas.height;
            ctx.clearRect(0, 0, w, h);
            for (var i = 0; i < stars.length; i++) {
                var st = stars[i];
                ctx.globalAlpha = reduceMotion ? 0.7 : 0.35 + 0.65 * Math.abs(Math.sin(t / 900 + st.p));
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(st.x, st.y, st.s, st.s);
            }
            if (!reduceMotion) requestAnimationFrame(draw);
        }
        resize();
        window.addEventListener('resize', resize);
        requestAnimationFrame(draw);
    }

    // --- Thermostat dial: creeps up, panics, resets ---------------------
    var art = document.querySelector('[data-dial]');
    if (art) {
        var needle = art.querySelector('.dial-needle');
        var label = art.querySelector('.dial-temp');
        var MIN = 50, MAX = 90, HOT = 80; // same range as the game itself
        var temp = 70;
        function render() {
            var angle = -120 + (temp - MIN) / (MAX - MIN) * 240;
            needle.style.transform = 'rotate(' + angle + 'deg)';
            label.textContent = temp + '°';
            art.classList.toggle('hot', temp >= HOT);
        }
        render();
        if (!reduceMotion) {
            setInterval(function () {
                temp += temp >= HOT ? 3 : Math.random() < 0.8 ? 1 : 2;
                if (temp > MAX) temp = 70; // someone finally fixed it
                render();
            }, 280);
        }
    }

    // --- Game select: arrow keys + Enter, like a real cabinet ------------
    var cards = Array.prototype.slice.call(document.querySelectorAll('.game-card.playable'));
    var idx = 0;
    function select(i) {
        cards.forEach(function (c, j) { c.classList.toggle('selected', j === i); });
        idx = i;
    }
    if (cards.length) {
        select(0);
        cards.forEach(function (c, i) {
            c.addEventListener('mouseenter', function () { select(i); });
            c.addEventListener('focus', function () { select(i); });
            c.addEventListener('click', function () {
                if (typeof gtag === 'function') gtag('event', 'game_select', { game_name: c.dataset.game });
            });
        });
        document.addEventListener('keydown', function (e) {
            var tag = (e.target && e.target.tagName) || '';
            if (tag === 'INPUT' || tag === 'TEXTAREA') return;
            if (e.key === 'ArrowRight') {
                select((idx + 1) % cards.length); cards[idx].focus(); e.preventDefault();
            } else if (e.key === 'ArrowLeft') {
                select((idx - 1 + cards.length) % cards.length); cards[idx].focus(); e.preventDefault();
            } else if (e.key === 'Enter' && document.activeElement === document.body) {
                cards[idx].click();
            }
        });
    }
})();
