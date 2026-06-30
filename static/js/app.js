document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const expectedInput = document.getElementById('expected_pdf');
    const actualInput = document.getElementById('actual_pdf');
    const expectedDrag = document.getElementById('expected-drag-zone');
    const actualDrag = document.getElementById('actual-drag-zone');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    const uploadView = document.getElementById('upload-view');
    const loadingView = document.getElementById('loading-view');
    const dashboardView = document.getElementById('dashboard-view');
    
    const resetBtn = document.getElementById('reset-btn');
    const downloadBtn = document.getElementById('download-btn');
    
    const mismatchCount = document.getElementById('mismatch-count');
    const filterPills = document.querySelectorAll('.filter-pill');
    const listContainer = document.getElementById('mismatches-list-container');
    
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const currentPageNum = document.getElementById('current-page-num');
    const totalPagesNum = document.getElementById('total-pages-num');
    
    const leftPageImg = document.getElementById('left-page-img');
    const rightPageImg = document.getElementById('right-page-img');
    const leftOverlay = document.getElementById('left-overlay-layer');
    const rightOverlay = document.getElementById('right-overlay-layer');
    
    const leftPanel = document.getElementById('reference-panel');
    const rightPanel = document.getElementById('actual-panel');

    // State Variables
    let leftPages = [];
    let rightPages = [];
    let differences = [];
    let currentLeftPage = 1;
    let currentRightPage = 1;
    let activeFilter = 'all';
    let activeDiffId = null;

    // Loading step elements
    const stepExtract = document.getElementById('step-extract');
    const stepAlign = document.getElementById('step-align');
    const stepCompare = document.getElementById('step-compare');
    const stepRender = document.getElementById('step-render');

    // Initialize Drag & Drop Events
    setupDragZone(expectedDrag, expectedInput);
    setupDragZone(actualDrag, actualInput);

    function setupDragZone(zone, input) {
        // Click to open file dialog
        zone.addEventListener('click', () => input.click());

        input.addEventListener('change', () => {
            handleFileSelect(zone, input.files[0]);
        });

        // Drag events
        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dragover');
            }, false);
        });

        zone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                input.files = files;
                handleFileSelect(zone, files[0]);
            }
        });
    }

    function handleFileSelect(zone, file) {
        if (!file || file.type !== 'application/pdf') {
            alert('Please select a valid PDF file.');
            return;
        }

        const previewInfo = zone.querySelector('.file-preview-info');
        const uploadContent = zone.querySelector('.upload-content');
        
        // Show file info preview
        previewInfo.style.display = 'flex';
        previewInfo.querySelector('.file-name').textContent = file.name;
        
        // Style adjustments
        zone.style.borderColor = 'var(--secondary)';
        
        // Check if both files are selected
        checkUploadReady();
    }

    function checkUploadReady() {
        if (expectedInput.files.length > 0 && actualInput.files.length > 0) {
            analyzeBtn.disabled = false;
        } else {
            analyzeBtn.disabled = true;
        }
    }

    // Run Analysis
    analyzeBtn.addEventListener('click', () => {
        if (expectedInput.files.length === 0 || actualInput.files.length === 0) return;

        const formData = new FormData();
        formData.append('expected_pdf', expectedInput.files[0]);
        formData.append('actual_pdf', actualInput.files[0]);

        // Transition views
        uploadView.style.display = 'none';
        loadingView.style.display = 'flex';
        resetBtn.style.display = 'none';
        downloadBtn.style.display = 'none';

        // Simulate step progress updates
        let stepInterval = startStepProgressSimulation();

        fetch('/api/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(stepInterval);
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error occurred') });
            }
            return response.json();
        })
        .then(data => {
            // Finish loading animation
            completeAllSteps();
            
            setTimeout(() => {
                leftPages = data.left_pages;
                rightPages = data.right_pages;
                differences = data.differences;

                // Configure buttons
                downloadBtn.href = data.download_url;
                downloadBtn.style.display = 'inline-flex';
                resetBtn.style.display = 'inline-flex';

                // Display dashboard
                loadingView.style.display = 'none';
                dashboardView.style.display = 'block';

                // Set total pages count based on Actual PDF (primary doc)
                totalPagesNum.textContent = rightPages.length;

                // Setup state
                currentLeftPage = 1;
                currentRightPage = 1;
                activeFilter = 'all';
                activeDiffId = null;

                renderMismatchList();
                renderPage(1, 1);
            }, 600);
        })
        .catch(err => {
            clearInterval(stepInterval);
            alert(`Analysis failed: ${err.message}`);
            loadingView.style.display = 'none';
            uploadView.style.display = 'flex';
        });
    });

    // Reset view for new comparison
    resetBtn.addEventListener('click', () => {
        uploadForm.reset();
        
        // Reset file dragzones
        document.querySelectorAll('.file-preview-info').forEach(info => info.style.display = 'none');
        document.querySelectorAll('.drag-zone').forEach(zone => {
            zone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        });

        analyzeBtn.disabled = true;
        resetBtn.style.display = 'none';
        downloadBtn.style.display = 'none';

        dashboardView.style.display = 'none';
        uploadView.style.display = 'flex';
        
        // Reset steps
        document.querySelectorAll('.step-item').forEach(step => {
            step.className = 'step-item';
        });
        stepExtract.className = 'step-item active';
    });

    // Step Progress Simulator
    function startStepProgressSimulation() {
        let currentStep = 1;
        
        const interval = setInterval(() => {
            if (currentStep === 1) {
                stepExtract.className = 'step-item completed';
                stepExtract.querySelector('i').className = 'fa-solid fa-circle-check';
                stepAlign.className = 'step-item active';
                currentStep = 2;
            } else if (currentStep === 2) {
                stepAlign.className = 'step-item completed';
                stepAlign.querySelector('i').className = 'fa-solid fa-circle-check';
                stepCompare.className = 'step-item active';
                currentStep = 3;
            } else if (currentStep === 3) {
                stepCompare.className = 'step-item completed';
                stepCompare.querySelector('i').className = 'fa-solid fa-circle-check';
                stepRender.className = 'step-item active';
                currentStep = 4;
            }
        }, 2200);

        return interval;
    }

    function completeAllSteps() {
        document.querySelectorAll('.step-item').forEach(step => {
            step.className = 'step-item completed';
            step.querySelector('i').className = 'fa-solid fa-circle-check';
        });
    }

    // Render side-by-side pages
    function renderPage(leftPageNum, rightPageNum) {
        currentLeftPage = leftPageNum;
        currentRightPage = rightPageNum;

        // Display current page based on Actual PDF (Right panel)
        currentPageNum.textContent = rightPageNum;

        // Load page images
        if (leftPageNum <= leftPages.length && leftPageNum > 0) {
            leftPanel.style.opacity = '1';
            leftPageImg.src = leftPages[leftPageNum - 1].url;
            leftPageImg.style.display = 'block';
            drawOverlays(leftOverlay, 'left', leftPageNum, leftPages[leftPageNum - 1]);
        } else {
            leftPageImg.style.display = 'none';
            leftOverlay.innerHTML = '';
            leftPanel.style.opacity = '0.3';
        }

        if (rightPageNum <= rightPages.length && rightPageNum > 0) {
            rightPanel.style.opacity = '1';
            rightPageImg.src = rightPages[rightPageNum - 1].url;
            rightPageImg.style.display = 'block';
            drawOverlays(rightOverlay, 'right', rightPageNum, rightPages[rightPageNum - 1]);
        } else {
            rightPageImg.style.display = 'none';
            rightOverlay.innerHTML = '';
            rightPanel.style.opacity = '0.3';
        }

        // Keep highlights active if relevant
        if (activeDiffId !== null) {
            const activeLeftBox = leftOverlay.querySelector(`.bbox-highlight[data-id="${activeDiffId}"]`);
            const activeRightBox = rightOverlay.querySelector(`.bbox-highlight[data-id="${activeDiffId}"]`);
            if (activeLeftBox) activeLeftBox.classList.add('active');
            if (activeRightBox) activeRightBox.classList.add('active');
        }
    }

    function drawOverlays(layer, side, pageNum, pageInfo) {
        layer.innerHTML = '';
        
        const pageW = pageInfo.width;
        const pageH = pageInfo.height;

        differences.forEach(diff => {
            const target = side === 'left' ? diff.left_target : diff.right_target;
            if (!target || target.page !== pageNum) return;

            const [x0, y0, x1, y1] = target.bbox;

            const leftPct = (x0 / pageW) * 100;
            const topPct = (y0 / pageH) * 100;
            const widthPct = ((x1 - x0) / pageW) * 100;
            const heightPct = ((y1 - y0) / pageH) * 100;

            const overlayBox = document.createElement('div');
            overlayBox.className = `bbox-highlight ${diff.severity}`;
            overlayBox.style.left = `${leftPct}%`;
            overlayBox.style.top = `${topPct}%`;
            overlayBox.style.width = `${widthPct}%`;
            overlayBox.style.height = `${heightPct}%`;
            overlayBox.setAttribute('data-id', diff.id);
            overlayBox.setAttribute('data-tooltip', `${diff.category.toUpperCase()}: ${diff.description}`);

            // Interaction
            overlayBox.addEventListener('click', () => {
                selectDifference(diff.id);
            });

            layer.appendChild(overlayBox);
        });
    }

    // Filter and Render Mismatch Cards
    function renderMismatchList() {
        listContainer.innerHTML = '';
        
        const filtered = differences.filter(diff => {
            if (activeFilter === 'all') return true;
            return diff.severity === activeFilter;
        });

        mismatchCount.textContent = filtered.length;

        if (filtered.length === 0) {
            listContainer.innerHTML = `
                <div class="step-item" style="justify-content: center; color: var(--text-muted);">
                    <i class="fa-solid fa-face-smile" style="display:inline; color: var(--secondary);"></i>
                    <span>No mismatches found for this filter.</span>
                </div>
            `;
            return;
        }

        filtered.forEach(diff => {
            const card = document.createElement('div');
            card.className = `mismatch-card ${activeDiffId === diff.id ? 'active' : ''}`;
            card.setAttribute('data-id', diff.id);

            // Icon by category
            let iconClass = 'fa-solid fa-file-invoice';
            if (diff.category === 'number') iconClass = 'fa-solid fa-hashtag';
            else if (diff.category === 'spelling') iconClass = 'fa-solid fa-spell-check';
            else if (diff.category === 'insertion') iconClass = 'fa-solid fa-circle-plus';
            else if (diff.category === 'deletion') iconClass = 'fa-solid fa-circle-minus';
            
            let pageText = 'Page';
            if (diff.left_target && diff.right_target) {
                pageText = diff.left_target.page === diff.right_target.page ? 
                    `Page ${diff.right_target.page}` : 
                    `Page ${diff.left_target.page} → ${diff.right_target.page}`;
            } else if (diff.right_target) {
                pageText = `Page ${diff.right_target.page}`;
            } else if (diff.left_target) {
                pageText = `Page ${diff.left_target.page}`;
            }

            card.innerHTML = `
                <div class="card-top">
                    <span class="card-title">
                        <span class="severity-indicator ${diff.severity}"></span>
                        <i class="${iconClass}"></i> ${diff.category.toUpperCase()}
                    </span>
                    <span class="card-page">${pageText}</span>
                </div>
                <div class="card-desc">${diff.description}</div>
                ${(diff.expected_text || diff.actual_text) ? `
                <div class="card-values">
                    <div class="val-box">
                        <span class="val-lbl">Expected</span>
                        <span class="val-txt expected" title="${diff.expected_text || 'None'}">${diff.expected_text || '—'}</span>
                    </div>
                    <div class="val-box">
                        <span class="val-lbl">Actual</span>
                        <span class="val-txt actual" title="${diff.actual_text || 'None'}">${diff.actual_text || '—'}</span>
                    </div>
                </div>` : ''}
            `;

            card.addEventListener('click', () => {
                selectDifference(diff.id);
            });

            listContainer.appendChild(card);
        });
    }

    function selectDifference(id) {
        activeDiffId = id;

        // Highlight card in list
        document.querySelectorAll('.mismatch-card').forEach(c => {
            c.classList.remove('active');
        });
        const activeCard = listContainer.querySelector(`.mismatch-card[data-id="${id}"]`);
        if (activeCard) {
            activeCard.classList.add('active');
            activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // Get mismatch target pages
        const diff = differences.find(d => d.id === id);
        let leftP = currentLeftPage;
        let rightP = currentRightPage;

        if (diff.left_target) leftP = diff.left_target.page;
        if (diff.right_target) rightP = diff.right_target.page;

        // Render targets
        renderPage(leftP, rightP);
    }

    // Filter click events
    filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeFilter = pill.getAttribute('data-filter');
            renderMismatchList();
        });
    });

    // Page controls navigation
    prevPageBtn.addEventListener('click', () => {
        let prevR = currentRightPage - 1;
        let prevL = currentLeftPage - 1;
        if (prevR < 1) prevR = 1;
        if (prevL < 1) prevL = 1;
        
        if (prevR !== currentRightPage || prevL !== currentLeftPage) {
            renderPage(prevL, prevR);
        }
    });

    nextPageBtn.addEventListener('click', () => {
        let nextR = currentRightPage + 1;
        let nextL = currentLeftPage + 1;
        if (nextR > rightPages.length) nextR = rightPages.length;
        if (nextL > leftPages.length) nextL = leftPages.length;
        
        if (nextR !== currentRightPage || nextL !== currentLeftPage) {
            renderPage(nextL, nextR);
        }
    });
});
