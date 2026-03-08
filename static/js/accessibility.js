(function () {
    // Create and inject accessibility styles
    const style = document.createElement('style');
    style.innerHTML = `
        .acc-widget-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background: #2563eb;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            transition: transform 0.2s;
            border: none;
        }
        .acc-widget-btn:hover { transform: scale(1.1); }
        .acc-menu {
            position: fixed;
            bottom: 80px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            padding: 15px;
            display: none;
            flex-direction: column;
            gap: 10px;
            z-index: 9999;
            width: 200px;
            border: 1px solid #e2e8f0;
        }
        .acc-menu.active { display: flex; }
        .acc-menu h4 { margin: 0 0 5px 0; font-size: 0.9rem; color: #64748b; }
        .acc-row { display: flex; gap: 5px; }
        .acc-btn {
            flex: 1;
            padding: 8px;
            border: 1px solid #e2e8f0;
            background: #f8fafc;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }
        .acc-btn:hover { background: #f1f5f9; }
        .acc-btn.active { background: #2563eb; color: white; border-color: #2563eb; }

        /* High Contrast Styles */
        body.high-contrast {
            background-color: #000 !important;
            color: #fff !important;
        }
        body.high-contrast * {
            background-color: #000 !important;
            color: #ffff00 !important;
            border-color: #ffff00 !important;
            box-shadow: none !important;
        }
        body.high-contrast a, body.high-contrast button {
            background-color: #000 !important;
            color: #00ffff !important;
            border: 2px solid #00ffff !important;
        }
        body.high-contrast img { filter: grayscale(100%) contrast(200%); }
    `;
    document.head.appendChild(style);

    // Create Widget DOM
    const widget = document.createElement('div');
    widget.innerHTML = `
        <button class="acc-widget-btn" id="accBtn" title="Accessibility Tools" aria-label="Accessibility Tools">
            <i class="fas fa-universal-access" style="font-size: 1.5rem;"></i>
        </button>
        <div class="acc-menu" id="accMenu">
            <h4>Text Size</h4>
            <div class="acc-row">
                <button class="acc-btn" id="fontDec"><i class="fas fa-minus"></i> A</button>
                <button class="acc-btn" id="fontInc"><i class="fas fa-plus"></i> A</button>
            </div>
            <h4>Visuals</h4>
            <button class="acc-btn" id="toggleContrast"><i class="fas fa-adjust"></i> High Contrast</button>
            <button class="acc-btn" id="resetAcc" style="margin-top: 5px; color: #ef4444;"><i class="fas fa-redo"></i> Reset</button>
        </div>
    `;
    document.body.appendChild(widget);

    const menu = document.getElementById('accMenu');
    const btn = document.getElementById('accBtn');
    let fontSize = parseInt(localStorage.getItem('acc-font-size')) || 100;
    let isHighContrast = localStorage.getItem('acc-contrast') === 'true';

    // Toggle menu
    btn.onclick = (e) => {
        e.stopPropagation();
        menu.classList.toggle('active');
    };

    document.onclick = (e) => {
        if (!menu.contains(e.target) && e.target !== btn) {
            menu.classList.remove('active');
        }
    };

    // Apply scaling
    const applyScaling = () => {
        document.documentElement.style.fontSize = fontSize + '%';
        localStorage.setItem('acc-font-size', fontSize);
    };

    // Apply contrast
    const applyContrast = () => {
        if (isHighContrast) {
            document.body.classList.add('high-contrast');
            document.getElementById('toggleContrast').classList.add('active');
        } else {
            document.body.classList.remove('high-contrast');
            document.getElementById('toggleContrast').classList.remove('active');
        }
        localStorage.setItem('acc-contrast', isHighContrast);
    };

    document.getElementById('fontInc').onclick = () => {
        if (fontSize < 150) fontSize += 10;
        applyScaling();
    };

    document.getElementById('fontDec').onclick = () => {
        if (fontSize > 80) fontSize -= 10;
        applyScaling();
    };

    document.getElementById('toggleContrast').onclick = () => {
        isHighContrast = !isHighContrast;
        applyContrast();
    };

    document.getElementById('resetAcc').onclick = () => {
        fontSize = 100;
        isHighContrast = false;
        applyScaling();
        applyContrast();
    };

    // Initial Apply
    applyScaling();
    applyContrast();
})();
