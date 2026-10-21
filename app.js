const i18n = {
    vi: {
        step1Title: "1. CHỌN GAME / ỨNG DỤNG",
        step2Title: "2. CHỌN VẬT PHẨM & MẶT HÀNG",
        allCat: "Tất Cả",
        noCat: "Chưa có danh mục nào trên hệ thống.",
        noProd: "Chưa có sản phẩm nào cho danh mục này.",
        stockLabel: "Còn",
        buyPackage: "MUA GÓI",
        buyAcc: "MUA ACC",
        accTitle: "KHO TÀI KHOẢN CAO CẤP",
        noAcc: "Chưa có tài khoản nào được mở bán.",
        depositTitle: "VIETQR MBBANK ĐỐI SOÁT TỰ ĐỘNG 24/7",
        depositSub: "Chuyển khoản bất kỳ số tiền nào. Hệ thống tự động nhận diện và cộng tiền trong 1 giây!",
        labelBank: "Ngân hàng:",
        labelStk: "Số tài khoản:",
        labelCtk: "Chủ tài khoản:",
        labelMemo: "Nội dung CK:",
        pollingTxt: "Đang tự động đối soát giao dịch ngân hàng thời gian thực (30s)...",
        depositHistTitle: "LỊCH SỬ NẠP CỦA BẠN",
        noDepositHist: "Chưa có giao dịch nạp.",
        leaderboardTitle: "TOP NẠP (TỪ 50.000Đ TRỞ LÊN)",
        noLeaderboard: "Chưa có thành viên nào đạt mốc nạp từ 50.000đ trở lên.",
        voucherTitle: "NHẬP MÃ VOUCHER / KHUYẾN MÃI",
        voucherBtn: "ÁP DỤNG",
        giftcodeTitle: "NHẬP MÃ GIFTCODE TRI ÂN",
        giftcodeBtn: "NHẬN",
        inventoryTitle: "KHO HÀNG CỦA BẠN (KEY / ACC)",
        inventorySub: "Đã lưu cả trong Chat Bot",
        noInventory: "Bạn chưa mua vật phẩm nào.",
        recentTxTitle: "GIAO DỊCH GẦN ĐÂY",
        noRecentTx: "Chưa có giao dịch gần đây.",
        navKey: "MUA KEY",
        navAcc: "MUA ACC",
        navDeposit: "NẠP TIỀN",
        navTop: "TOP NẠP",
        navProfile: "CÁ NHÂN",
        modalConfirm: "Xác Nhận Mua",
        modalCancel: "HUỶ",
        modalBuy: "MUA NGAY",
        modalHelp: "Key sẽ được cấp ngay trên màn hình và gửi trực tiếp vào tin nhắn Telegram của bạn.",
        verifiedHeading: "XÁC MINH DANH TÍNH",
        verifiedDesc: "Tài khoản của bạn đã được kết nối an toàn với máy chủ Telegram. Mọi giao dịch nạp tiền VietQR và mua key đều được bảo vệ và tự động hoá 100%.",
        verifiedClose: "ĐÃ HIỂU",
        roleCustomer: "THÀNH VIÊN",
        roleSeller: "SELLER VIP",
        roleAdmin: "QUẢN TRỊ VIÊN"
    },
    en: {
        step1Title: "1. SELECT GAME / APPLICATION",
        step2Title: "2. SELECT PRODUCT & PACKAGE",
        allCat: "All",
        noCat: "No categories available yet.",
        noProd: "No products available in this category.",
        stockLabel: "Stock",
        buyPackage: "BUY",
        buyAcc: "BUY ACC",
        accTitle: "PREMIUM ACCOUNT STORE",
        noAcc: "No accounts available for sale.",
        depositTitle: "VIETQR MBBANK AUTO DEPOSIT 24/7",
        depositSub: "Transfer any amount. The system automatically verifies and credits your balance in 1 second!",
        labelBank: "Bank:",
        labelStk: "Account No:",
        labelCtk: "Account Name:",
        labelMemo: "Transfer Memo:",
        pollingTxt: "Auto-verifying real-time bank transactions (30s)...",
        depositHistTitle: "YOUR DEPOSIT HISTORY",
        noDepositHist: "No deposit transactions yet.",
        leaderboardTitle: "TOP DEPOSITS (MIN 50,000 VND)",
        noLeaderboard: "No users in Top Deposits yet (Min deposit: 50,000 VND).",
        voucherTitle: "ENTER VOUCHER / PROMO CODE",
        voucherBtn: "APPLY",
        giftcodeTitle: "ENTER REWARD GIFTCODE",
        giftcodeBtn: "CLAIM",
        inventoryTitle: "YOUR INVENTORY (KEY / ACC)",
        inventorySub: "Also saved in Telegram Chat",
        noInventory: "You have not purchased any items yet.",
        recentTxTitle: "RECENT TRANSACTIONS",
        noRecentTx: "No recent transactions.",
        navKey: "BUY KEY",
        navAcc: "BUY ACC",
        navDeposit: "DEPOSIT",
        navTop: "TOP RANK",
        navProfile: "PROFILE",
        modalConfirm: "Confirm Purchase",
        modalCancel: "CANCEL",
        modalBuy: "BUY NOW",
        modalHelp: "The key will be delivered on screen and sent directly to your Telegram chat.",
        verifiedHeading: "IDENTITY VERIFICATION",
        verifiedDesc: "Your account is securely synchronized with Telegram servers. All key purchases and bank deposits are encrypted and 100% automated.",
        verifiedClose: "GOT IT",
        roleCustomer: "MEMBER",
        roleSeller: "SELLER VIP",
        roleAdmin: "ADMINISTRATOR"
    }
};

let currentLang = localStorage.getItem('store_lang') || 'vi';

let appData = {
    shopInfo: {
        name: "",
        notice: "",
        bankCode: "",
        bankAccount: "",
        accountName: ""
    },
    bankApi: { prefix: "" },
    musicUrl: "",
    categories: [],
    products: [],
    recentTransactions: [],
    topDepositors: [],
    user: {
        id: "0",
        name: "Khách hàng",
        avatar: "",
        balance: 0,
        spent: 0,
        totalDeposit: 0,
        role: "customer",
        inventory: [],
        depositHistory: []
    }
};

let selectedCategoryId = "all";
let activeTab = "mua-key";
let selectedProductForPurchase = null;
let isBgmPlaying = false;
let autoDepositPollingInterval = null;
const bgmAudio = document.getElementById('bgmAudio');

function lay_header_bao_mat(extra) {
    const h = extra ? { ...extra } : {};
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
        h['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    }
    return h;
}

function dat_ngon_ngu(lang) {
    currentLang = lang;
    localStorage.setItem('store_lang', lang);
    const btnVi = document.getElementById('langBtnVi');
    const btnEn = document.getElementById('langBtnEn');
    if (btnVi && btnEn) {
        if (lang === 'vi') {
            btnVi.className = "px-1.5 py-0.5 rounded bg-cyan-400 text-black transition";
            btnEn.className = "px-1.5 py-0.5 rounded text-gray-400 hover:text-white transition";
        } else {
            btnEn.className = "px-1.5 py-0.5 rounded bg-cyan-400 text-black transition";
            btnVi.className = "px-1.5 py-0.5 rounded text-gray-400 hover:text-white transition";
        }
    }
    ap_dung_ngon_ngu();
    lam_moi_toan_bo_giao_dien();
}

function ap_dung_ngon_ngu() {
    const t = i18n[currentLang] || i18n.vi;
    const setTxt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };
    setTxt('txt-step1-title', t.step1Title);
    setTxt('txt-step2-title', t.step2Title);
    setTxt('txt-acc-title', t.accTitle);
    setTxt('txt-deposit-title', t.depositTitle);
    setTxt('txt-deposit-sub', t.depositSub);
    setTxt('txt-label-bank', t.labelBank);
    setTxt('txt-label-stk', t.labelStk);
    setTxt('txt-label-ctk', t.labelCtk);
    setTxt('txt-label-memo', t.labelMemo);
    setTxt('txt-polling-status', t.pollingTxt);
    setTxt('txt-deposit-history-title', t.depositHistTitle);
    setTxt('txt-leaderboard-title', t.leaderboardTitle);
    setTxt('txt-voucher-title', t.voucherTitle);
    setTxt('txt-voucher-btn', t.voucherBtn);
    setTxt('txt-giftcode-title', t.giftcodeTitle);
    setTxt('txt-giftcode-btn', t.giftcodeBtn);
    setTxt('txt-inventory-title', t.inventoryTitle);
    setTxt('txt-inventory-sub', t.inventorySub);
    setTxt('txt-recent-tx-title', t.recentTxTitle);
    setTxt('txt-nav-key', t.navKey);
    setTxt('txt-nav-acc', t.navAcc);
    setTxt('txt-nav-deposit', t.navDeposit);
    setTxt('txt-nav-top', t.navTop);
    setTxt('txt-nav-profile', t.navProfile);
    setTxt('modalProdHelpTxt', t.modalHelp);
    setTxt('modalBtnCancel', t.modalCancel);
    setTxt('modalBtnConfirm', t.modalBuy);
    setTxt('modalVerifiedHeading', t.verifiedHeading);
    setTxt('modalVerifiedDesc', t.verifiedDesc);
}

function dinh_dang_thoi_gian(dur) {
    const d = (dur || '').toString().toLowerCase().trim();
    const isEn = (currentLang === 'en');
    if (d === '1h' || d === '1gio') return isEn ? '1 Hour' : '1 Giờ';
    if (d === '2h' || d === '2gio') return isEn ? '2 Hours' : '2 Giờ';
    if (d === '3h' || d === '3gio') return isEn ? '3 Hours' : '3 Giờ';
    if (d === '1d' || d === '1ngay' || d === '1day') return isEn ? '1 Day' : '1 Ngày';
    if (d === '3d' || d === '3ngay') return isEn ? '3 Days' : '3 Ngày';
    if (d === '7d' || d === '7ngay' || d === '1tuan') return isEn ? '7 Days' : '7 Ngày';
    if (d === '30d' || d === '1thang' || d === '30ngay') return isEn ? '30 Days' : '30 Ngày';
    if (d === 'vv' || d === 'vinhvien') return isEn ? 'Permanent' : 'Vĩnh Viễn';
    if (d.endsWith('h')) return d.replace('h', '') + ' ' + (isEn ? 'Hours' : 'Giờ');
    if (d.endsWith('d')) return d.replace('d', '') + ' ' + (isEn ? 'Days' : 'Ngày');
    return dur || (isEn ? '1 Day' : '1 Ngày');
}

function bat_buoc_truy_cap_dien_thoai() {
    const urlParams = new URLSearchParams(window.location.search);
    const isPreview = urlParams.get('preview') === '1' || urlParams.get('admin') === '1';
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (isPreview || isLocalhost) {
        return true;
    }

    const tgPlatform = window.Telegram?.WebApp?.platform;
    const ua = (navigator.userAgent || navigator.vendor || window.opera || "").toLowerCase();
    const isTgDesktop = (tgPlatform === 'tdesktop' || tgPlatform === 'macos' || tgPlatform === 'web' || tgPlatform === 'weba');
    const isMobileDevice = /android|iphone|ipad|ipod|mobile/i.test(ua);
    const isSmallScreen = window.innerWidth <= 820;
    if (isTgDesktop || (!isMobileDevice && !isSmallScreen)) {
        const pcScreen = document.getElementById('pcBlockScreen');
        const appContainer = document.getElementById('appContainer');
        const splash = document.getElementById('splashScreen');
        if (splash) splash.classList.add('hidden');
        if (appContainer) appContainer.classList.add('hidden');
        if (pcScreen) {
            pcScreen.classList.remove('hidden');
            pcScreen.classList.add('flex');
        }
        return false;
    }
    return true;
}

async function kiem_tra_bao_mat_client() {
    try {
        const res = await fetch('/api/check-security');
        const data = await res.json();
        if (data.vpn_detected) {
            const lockScreen = document.getElementById('vpnLockScreen');
            if (lockScreen) {
                lockScreen.classList.remove('hidden');
                lockScreen.classList.add('flex');
            }
            return false;
        }
    } catch (e) {}
    return true;
}

function thong_bao_hoat_dong_admin(type) {
    try {
        fetch('/api/notify-activity', {
            method: 'POST',
            headers: lay_header_bao_mat({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                type: type,
                user_id: appData.user.id,
                user_name: appData.user.name
            })
        });
    } catch (e) {}
}

function chuyen_doi_html(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function dinh_dang_tien_vnd(amount) {
    return new Intl.NumberFormat('vi-VN').format(amount || 0) + 'đ';
}

function hien_thong_bao(msg) {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.remove('opacity-0', 'pointer-events-none');
    toast.classList.add('opacity-100');
    setTimeout(() => {
        toast.classList.remove('opacity-100');
        toast.classList.add('opacity-0', 'pointer-events-none');
    }, 2500);
}

function sao_chep_vao_khay_nho(elementId, successMsg) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => hien_thong_bao(successMsg || 'Đã sao chép!'));
    } else {
        const temp = document.createElement('textarea');
        temp.value = text;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
        hien_thong_bao(successMsg || 'Đã sao chép!');
    }
}

function mo_hop_thoai_xac_minh() {
    const modal = document.getElementById('verifiedModal');
    const nameEl = document.getElementById('modalVerifiedName');
    const uidEl = document.getElementById('modalVerifiedUid');
    const roleEl = document.getElementById('modalVerifiedRole');
    const t = i18n[currentLang] || i18n.vi;
    if (nameEl) nameEl.innerText = appData.user.name || "User";
    if (uidEl) uidEl.innerText = appData.user.id || "...";
    if (roleEl) {
        if (appData.user.role === 'seller') {
            roleEl.innerText = t.roleSeller;
            roleEl.className = "text-amber-400 font-bold";
        } else {
            roleEl.innerText = t.roleCustomer;
            roleEl.className = "text-cyan-300 font-bold";
        }
    }
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function dong_hop_thoai_xac_minh() {
    const modal = document.getElementById('verifiedModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function thiet_lap_nhac_nen(url) {
    if (!url || !bgmAudio) return;
    bgmAudio.src = url;
    bgmAudio.loop = true;
    bgmAudio.volume = 0.5;
    thu_tu_dong_phat_nhac();
}

function thu_tu_dong_phat_nhac() {
    if (!bgmAudio || !bgmAudio.src) return;
    bgmAudio.play().then(() => {
        isBgmPlaying = true;
        cap_nhat_giao_dien_nhac(true);
    }).catch(() => {
        isBgmPlaying = false;
        cap_nhat_giao_dien_nhac(false);
        const unlock = () => {
            if (bgmAudio.src && !isBgmPlaying) {
                bgmAudio.play().then(() => {
                    isBgmPlaying = true;
                    cap_nhat_giao_dien_nhac(true);
                }).catch(() => {});
            }
            document.removeEventListener('pointerdown', unlock);
            document.removeEventListener('touchstart', unlock);
            document.removeEventListener('click', unlock);
        };
        document.addEventListener('pointerdown', unlock, { once: true });
        document.addEventListener('touchstart', unlock, { once: true });
        document.addEventListener('click', unlock, { once: true });
    });
}

function bat_tat_nhac_nen() {
    if (!bgmAudio || !bgmAudio.src) {
        hien_thong_bao(currentLang === 'en' ? "No music available!" : "Chưa có nhạc nền!");
        return;
    }
    if (isBgmPlaying) {
        bgmAudio.pause();
        isBgmPlaying = false;
        cap_nhat_giao_dien_nhac(false);
    } else {
        bgmAudio.play().then(() => {
            isBgmPlaying = true;
            cap_nhat_giao_dien_nhac(true);
        }).catch(() => {
            hien_thong_bao(currentLang === 'en' ? "Tap screen to allow music!" : "Chạm màn hình để cấp quyền phát nhạc!");
        });
    }
}

function cap_nhat_giao_dien_nhac(playing) {
    const icon = document.getElementById('bgmDiscIcon');
    const eq = document.getElementById('bgmEqualizer');
    const widget = document.getElementById('bgmControlWidget');
    if (playing) {
        if (icon) icon.classList.add('disc-spin');
        if (eq) eq.classList.remove('opacity-40');
        if (widget) widget.classList.add('border-cyan-400');
    } else {
        if (icon) icon.classList.remove('disc-spin');
        if (eq) eq.classList.add('opacity-40');
        if (widget) widget.classList.remove('border-cyan-400');
    }
}

function chuyen_tab(tabName) {
    activeTab = tabName;
    const tabIds = ['mua-key', 'mua-acc', 'nap-tien', 'top-nap', 'ca-nhan'];
    tabIds.forEach(t => {
        const tabEl = document.getElementById('tab-' + t);
        const navEl = document.getElementById('nav-' + t);
        if (tabEl) {
            if (t === tabName) tabEl.classList.remove('hidden');
            else tabEl.classList.add('hidden');
        }
        if (navEl) {
            if (t === tabName) {
                navEl.className = "btn-press flex flex-col items-center gap-0.5 text-cyan-400 font-bold";
            } else {
                navEl.className = "btn-press flex flex-col items-center gap-0.5 text-gray-400 hover:text-white font-medium";
            }
        }
    });
    if (tabName === 'nap-tien') {
        thong_bao_hoat_dong_admin('view_deposit');
        bat_dau_kiem_tra_nap_tien();
    } else {
        dung_kiem_tra_nap_tien();
    }
}

function hien_thi_thong_tin_nguoi_dung() {
    const nameEl = document.getElementById('userNameDisplay');
    const idEl = document.getElementById('userIdDisplay');
    const balEl = document.getElementById('userBalanceDisplay');
    const avtEl = document.getElementById('userAvatar');
    const roleBadge = document.getElementById('userRoleBadge');
    const verLabel = document.getElementById('userVerifiedLabel');
    if (nameEl) nameEl.innerText = appData.user.name || "Khách hàng";
    if (idEl) idEl.innerText = appData.user.id || "...";
    if (balEl) balEl.innerText = dinh_dang_tien_vnd(appData.user.balance || 0);
    if (avtEl) {
        avtEl.src = appData.user.avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + (appData.user.id || 'user');
    }
    if (roleBadge) {
        if (appData.user.role === 'seller') roleBadge.classList.remove('hidden');
        else roleBadge.classList.add('hidden');
    }
    if (verLabel) {
        if (appData.user.role === 'seller') {
            verLabel.className = "btn-press cursor-pointer flex items-center justify-end gap-1 mt-0.5 text-[8px] font-extrabold text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded-full border border-amber-500/40";
            verLabel.innerHTML = '<i class="fa-solid fa-crown text-amber-400"></i> SELLER VIP';
        } else {
            verLabel.className = "btn-press cursor-pointer flex items-center justify-end gap-1 mt-0.5 text-[8px] font-extrabold text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded-full border border-cyan-500/40";
            verLabel.innerHTML = '<i class="fa-solid fa-circle-check text-cyan-400"></i> VERIFIED';
        }
    }
}

function hien_thi_danh_muc() {
    const container = document.getElementById('categoryListContainer');
    const countBadge = document.getElementById('catCountBadge');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const catList = appData.categories || [];
    if (countBadge) countBadge.innerText = catList.length + ' ' + (currentLang === 'en' ? 'items' : 'mục');
    if (catList.length === 0) {
        container.innerHTML = '<div class="py-2 text-xs text-gray-500 italic">' + t.noCat + '</div>';
        return;
    }
    const isAllSelected = (selectedCategoryId === 'all' || !selectedCategoryId);
    const allBtn = document.createElement('div');
    allBtn.className = 'btn-press cursor-pointer flex-shrink-0 px-3 py-1.5 rounded-xl flex items-center gap-2 border transition ' + (isAllSelected ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold' : 'bg-[#080c14] border-[#1a2a44] text-gray-400');
    allBtn.onclick = () => { selectedCategoryId = 'all'; hien_thi_danh_muc(); hien_thi_san_pham(); };
    allBtn.innerHTML = '<i class="fa-solid fa-layer-group text-xs ' + (isAllSelected ? 'text-cyan-300' : 'text-gray-400') + '"></i><span class="text-xs font-semibold whitespace-nowrap">' + t.allCat + '</span>';
    container.appendChild(allBtn);
    catList.forEach((cat) => {
        const isSelected = selectedCategoryId === cat.id;
        const card = document.createElement('div');
        card.className = 'btn-press cursor-pointer flex-shrink-0 px-3 py-1.5 rounded-xl flex items-center gap-2 border transition ' + (isSelected ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold' : 'bg-[#080c14] border-[#1a2a44] text-gray-400');
        card.onclick = () => { selectedCategoryId = cat.id; hien_thi_danh_muc(); hien_thi_san_pham(); };
        const iconHtml = cat.icon && cat.icon.startsWith('http') ? '<img src="' + chuyen_doi_html(cat.icon) + '" class="w-3.5 h-3.5 rounded object-cover">' : '<i class="fa-solid ' + chuyen_doi_html(cat.icon || 'fa-gamepad') + ' text-xs"></i>';
        card.innerHTML = '<div class="flex items-center justify-center">' + iconHtml + '</div><span class="text-xs whitespace-nowrap">' + chuyen_doi_html(cat.name) + '</span>';
        container.appendChild(card);
    });
}

function hien_thi_san_pham() {
    const container = document.getElementById('productListContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const allProds = appData.products || [];
    const filtered = allProds.filter(p => {
        if (p.type === 'acc') return false;
        if (!selectedCategoryId || selectedCategoryId === 'all') return true;
        return p.categoryId === selectedCategoryId;
    });
    if (filtered.length === 0) {
        container.innerHTML = '<div class="text-center py-6 text-xs text-gray-500 space-y-1"><i class="fa-solid fa-box-open text-xl opacity-40"></i><p>' + t.noProd + '</p></div>';
        return;
    }
    const grouped = {};
    filtered.forEach(p => {
        const rootName = p.name.trim();
        if (!grouped[rootName]) grouped[rootName] = [];
        grouped[rootName].push(p);
    });
    Object.keys(grouped).forEach(prodName => {
        const packageList = grouped[prodName];
        const card = document.createElement('div');
        card.className = "w-full p-3.5 rounded-2xl bg-[#080c14] border border-[#1a2a44] shadow-sm space-y-2.5";
        let packagesHtml = "";
        packageList.forEach(pkg => {
            const isSeller = appData.user.role === 'seller';
            const effectivePrice = isSeller && pkg.sellerPrice ? pkg.sellerPrice : pkg.price;
            const durationLabel = dinh_dang_thoi_gian(pkg.duration);
            packagesHtml += '<div class="w-full p-2.5 rounded-xl bg-[#0e1624] border border-[#1a2a44] flex items-center justify-between gap-2 hover:border-cyan-500/40 transition"><div><span class="px-2 py-0.5 rounded-md bg-cyan-950 text-cyan-300 border border-cyan-800/40 text-[10px] font-bold"><i class="fa-regular fa-clock text-[9px] mr-1"></i>' + chuyen_doi_html(durationLabel) + '</span><div class="flex items-center gap-1.5 mt-1"><span class="text-xs font-bold text-cyan-400 font-num">' + dinh_dang_tien_vnd(effectivePrice) + '</span>' + (isSeller && pkg.sellerPrice ? '<span class="text-[9px] text-gray-500 line-through font-num">' + dinh_dang_tien_vnd(pkg.price) + '</span>' : '') + '<span class="text-[9px] text-gray-400">• ' + t.stockLabel + ': <strong class="text-white font-num">' + (pkg.stock || 0) + '</strong></span></div></div><button onclick="bat_dau_mua_hang(\'' + chuyen_doi_html(pkg.id) + '\')" class="btn-press px-3.5 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-[10px] uppercase tracking-wider shrink-0 shadow-md">' + t.buyPackage + '</button></div>';
        });
        card.innerHTML = '<div class="flex items-center justify-between border-b border-[#1a2a44] pb-2"><h4 class="text-xs font-bold text-white flex items-center gap-1.5 truncate"><i class="fa-solid fa-bolt text-cyan-400 text-[11px]"></i>' + chuyen_doi_html(prodName) + '</h4><span class="text-[9px] text-gray-400 font-num">' + packageList.length + ' ' + (currentLang === 'en' ? 'packages' : 'gói') + '</span></div><div class="space-y-1.5">' + packagesHtml + '</div>';
        container.appendChild(card);
    });
}

function hien_thi_danh_sach_acc() {
    const container = document.getElementById('accListContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const accProds = (appData.products || []).filter(p => p.type === 'acc');
    if (accProds.length === 0) {
        container.innerHTML = '<div class="text-center py-6 text-xs text-gray-500 space-y-1"><i class="fa-solid fa-id-card text-xl opacity-40"></i><p>' + t.noAcc + '</p></div>';
        return;
    }
    accProds.forEach(p => {
        const isSeller = appData.user.role === 'seller';
        const effectivePrice = isSeller && p.sellerPrice ? p.sellerPrice : p.price;
        const item = document.createElement('div');
        item.className = "w-full p-3 rounded-2xl bg-[#080c14] border border-[#1a2a44] flex items-center justify-between gap-3 shadow-sm";
        item.innerHTML = '<div class="min-w-0"><h4 class="text-xs font-bold text-white truncate">' + chuyen_doi_html(p.name) + '</h4><div class="flex items-center gap-2 mt-1"><span class="text-xs font-bold text-cyan-400 font-num">' + dinh_dang_tien_vnd(effectivePrice) + '</span><span class="text-[10px] text-gray-400">• ' + t.stockLabel + ': <strong class="text-white font-num">' + (p.stock || 0) + '</strong></span></div></div><button onclick="bat_dau_mua_hang(\'' + chuyen_doi_html(p.id) + '\')" class="btn-press px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-[11px] uppercase tracking-wider shrink-0 shadow-md">' + t.buyAcc + '</button>';
        container.appendChild(item);
    });
}

function hien_thi_tab_nap_tien() {
    const bankAccTxt = document.getElementById('depositBankAccTxt');
    const accNameTxt = document.getElementById('depositAccountNameTxt');
    const syntaxTxt = document.getElementById('depositSyntaxTxt');
    const qrImg = document.getElementById('vietQrAutoImg');
    const bank = appData.shopInfo.bankCode || "";
    const acc = appData.shopInfo.bankAccount || "";
    const name = appData.shopInfo.accountName || "";
    const prefix = appData.bankApi.prefix || "";
    const uid = appData.user.id || "0";
    const syntax = prefix + ' ' + uid;
    if (bankAccTxt) bankAccTxt.innerText = acc;
    if (accNameTxt) accNameTxt.innerText = name;
    if (syntaxTxt) syntaxTxt.innerText = syntax;
    if (qrImg) {
        const encodedName = encodeURIComponent(name);
        const encodedSyntax = encodeURIComponent(syntax);
        qrImg.src = 'https://img.vietqr.io/image/' + bank + '-' + acc + '-compact2.jpg?addInfo=' + encodedSyntax + '&accountName=' + encodedName;
    }
    hien_thi_lich_su_nap();
}

function hien_thi_lich_su_nap() {
    const container = document.getElementById('depositHistoryContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const history = appData.user.depositHistory || [];
    if (history.length === 0) {
        container.innerHTML = '<p class="text-center py-2 text-[11px] text-gray-500">' + t.noDepositHist + '</p>';
        return;
    }
    history.slice(0, 5).forEach(h => {
        const row = document.createElement('div');
        row.className = "w-full p-2 rounded-lg bg-[#080c14] border border-[#1a2a44] flex items-center justify-between text-xs";
        row.innerHTML = '<div><div class="font-bold text-emerald-400 font-num">+' + dinh_dang_tien_vnd(h.amount) + '</div><div class="text-[9px] text-gray-500">' + chuyen_doi_html(h.time || '') + '</div></div><span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40">' + chuyen_doi_html(h.status || 'Success') + '</span>';
        container.appendChild(row);
    });
}

function hien_thi_bang_xep_hang() {
    const container = document.getElementById('leaderboardListContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const topUsers = appData.topDepositors || [];
    if (topUsers.length === 0) {
        container.innerHTML = '<div class="text-center py-8 text-xs text-gray-500 space-y-2"><i class="fa-solid fa-medal text-2xl text-amber-400/40"></i><p>' + t.noLeaderboard + '</p></div>';
        return;
    }
    topUsers.forEach((u, index) => {
        const rankNum = index + 1;
        let rankBadgeBg = "bg-slate-800 text-gray-300 border-slate-700";
        if (rankNum === 1) rankBadgeBg = "bg-amber-400 text-black border-amber-300 shadow-[0_0_10px_rgba(251,191,36,0.5)]";
        if (rankNum === 2) rankBadgeBg = "bg-gray-300 text-black border-white shadow-[0_0_10px_rgba(255,255,255,0.4)]";
        if (rankNum === 3) rankBadgeBg = "bg-amber-700 text-amber-100 border-amber-600";
        const isSeller = (u.role === 'seller');
        const row = document.createElement('div');
        row.className = "w-full p-3 rounded-xl bg-[#080c14] border border-[#1a2a44] flex items-center justify-between";
        const uidStr = String(u.id || '');
        const maskedId = uidStr.length > 5 ? uidStr.slice(0, 3) + '...' + uidStr.slice(-3) : uidStr;
        row.innerHTML = '<div class="flex items-center gap-2.5"><span class="w-6 h-6 rounded-full ' + rankBadgeBg + ' font-bold text-xs flex items-center justify-center font-num border">' + rankNum + '</span><div><div class="text-xs font-bold text-white flex items-center gap-1">' + chuyen_doi_html(u.name) + (isSeller ? '<span class="text-[8px] px-1 bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded">VIP</span>' : '') + '</div><div class="text-[9px] text-gray-500 font-num">ID: ' + chuyen_doi_html(maskedId) + '</div></div></div><span class="text-xs font-bold text-cyan-400 font-num">' + dinh_dang_tien_vnd(u.totalDeposit) + '</span>';
        container.appendChild(row);
    });
}

function hien_thi_kho_hang() {
    const container = document.getElementById('userInventoryContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const inv = appData.user.inventory || [];
    if (inv.length === 0) {
        container.innerHTML = '<p class="text-center py-3 text-[11px] text-gray-500">' + t.noInventory + '</p>';
        return;
    }
    inv.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = "w-full p-2.5 rounded-xl bg-[#080c14] border border-[#1a2a44] space-y-1.5";
        card.innerHTML = '<div class="flex items-center justify-between text-xs"><strong class="text-white">' + chuyen_doi_html(item.productName) + '</strong><span class="text-[9px] text-gray-500 font-num">' + chuyen_doi_html(item.time || '') + '</span></div><div class="flex items-center justify-between bg-black/40 p-2 rounded-lg border border-[#1a2a44]"><span id="invKeyTxt_' + index + '" class="text-[11px] font-num text-cyan-300 select-all truncate">' + chuyen_doi_html(item.secretKey) + '</span><button onclick="sao_chep_vao_khay_nho(\'invKeyTxt_' + index + '\', \'Đã sao chép!\')" class="text-cyan-400 hover:text-white text-xs px-1"><i class="fa-regular fa-copy"></i></button></div>';
        container.appendChild(card);
    });
}

function hien_thi_giao_dich_gan_day() {
    const container = document.getElementById('recentTxContainer');
    const t = i18n[currentLang] || i18n.vi;
    if (!container) return;
    container.innerHTML = '';
    const txs = appData.recentTransactions || [];
    if (txs.length === 0) {
        container.innerHTML = '<p class="text-center py-2 text-[11px] text-gray-500">' + t.noRecentTx + '</p>';
        return;
    }
    txs.forEach(tItem => {
        const row = document.createElement('div');
        row.className = "w-full p-2 rounded-lg bg-[#080c14] border border-[#1a2a44] flex items-center justify-between text-xs";
        row.innerHTML = '<div class="flex items-center gap-2"><i class="fa-solid ' + (tItem.type === 'nạp' ? 'fa-wallet text-emerald-400' : 'fa-cart-shopping text-cyan-400') + '"></i><span class="font-semibold text-white">' + chuyen_doi_html(tItem.name) + '</span><span class="text-gray-400">' + (tItem.type === 'nạp' ? (currentLang === 'en' ? 'deposited' : 'nạp') : (currentLang === 'en' ? 'bought' : 'mua')) + '</span><span class="font-bold ' + (tItem.type === 'nạp' ? 'text-emerald-400' : 'text-cyan-400') + ' font-num">' + dinh_dang_tien_vnd(tItem.amount) + '</span></div><span class="text-[10px] text-gray-500 font-num">' + chuyen_doi_html(tItem.time || '') + '</span>';
        container.appendChild(row);
    });
}

function lam_moi_toan_bo_giao_dien() {
    const noticeEl = document.getElementById('shopNoticeDisplay');
    if (noticeEl) noticeEl.innerText = appData.shopInfo.notice || "";
    hien_thi_thong_tin_nguoi_dung();
    hien_thi_danh_muc();
    hien_thi_san_pham();
    hien_thi_danh_sach_acc();
    hien_thi_tab_nap_tien();
    hien_thi_bang_xep_hang();
    hien_thi_kho_hang();
    hien_thi_giao_dich_gan_day();
}

function bat_dau_mua_hang(prodId) {
    const prod = appData.products.find(p => p.id === prodId);
    if (!prod) return;
    selectedProductForPurchase = prod;
    const isSeller = appData.user.role === 'seller';
    const price = isSeller && prod.sellerPrice ? prod.sellerPrice : prod.price;
    const modal = document.getElementById('purchaseModal');
    const titleEl = document.getElementById('modalProdTitle');
    const durBadge = document.getElementById('modalProdDurationBadge');
    const priceEl = document.getElementById('modalProdPrice');
    if (titleEl) titleEl.innerText = prod.name;
    if (durBadge) durBadge.innerText = dinh_dang_thoi_gian(prod.duration);
    if (priceEl) priceEl.innerText = dinh_dang_tien_vnd(price);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function dong_hop_thoai_mua_hang() {
    const modal = document.getElementById('purchaseModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    selectedProductForPurchase = null;
}

async function xac_nhan_mua_hang() {
    if (!selectedProductForPurchase) return;
    const prod = selectedProductForPurchase;
    dong_hop_thoai_mua_hang();
    try {
        const res = await fetch('/api/purchase', {
            method: 'POST',
            headers: lay_header_bao_mat({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                uid: appData.user.id,
                prod_id: prod.id,
                user_name: appData.user.name
            })
        });
        const result = await res.json();
        if (result.success) {
            hien_thong_bao(currentLang === 'en' ? "Purchase successful! Key sent to Telegram chat." : "Mua thành công! Key đã được gửi vào tin nhắn Telegram.");
            appData.user.balance = result.balance;
            await dong_bo_thong_tin_nguoi_dung();
            await dong_bo_du_lieu_cua_hang();
            lam_moi_toan_bo_giao_dien();
        } else {
            hien_thong_bao(result.message || "Lỗi giao dịch!");
        }
    } catch (e) {
        hien_thong_bao(currentLang === 'en' ? "Server connection error!" : "Lỗi kết nối máy chủ!");
    }
}

async function nhap_ma_thuong(type) {
    const inputId = type === 'voucher' ? 'voucherCodeInput' : 'giftcodeInput';
    const inputEl = document.getElementById(inputId);
    const code = inputEl?.value?.trim();
    if (!code) {
        hien_thong_bao(currentLang === 'en' ? "Please enter a code!" : "Vui lòng nhập mã!");
        return;
    }
    try {
        const res = await fetch('/api/redeem-code', {
            method: 'POST',
            headers: lay_header_bao_mat({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                user_id: appData.user.id,
                code: code,
                type: type
            })
        });
        const result = await res.json();
        if (result.success) {
            hien_thong_bao(result.message);
            if (inputEl) inputEl.value = '';
            await dong_bo_thong_tin_nguoi_dung();
            lam_moi_toan_bo_giao_dien();
        } else {
            hien_thong_bao(result.message || "Mã không hợp lệ!");
        }
    } catch (e) {
        hien_thong_bao("Lỗi kết nối máy chủ!");
    }
}

function dung_kiem_tra_nap_tien() {
    if (autoDepositPollingInterval) {
        clearInterval(autoDepositPollingInterval);
        autoDepositPollingInterval = null;
    }
}

function bat_dau_kiem_tra_nap_tien() {
    dung_kiem_tra_nap_tien();
    autoDepositPollingInterval = setInterval(async () => {
        if (!appData.user.id || activeTab !== 'nap-tien') return;
        try {
            const res = await fetch('/api/check-deposit', {
                method: 'POST',
                headers: lay_header_bao_mat({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({
                    user_id: appData.user.id,
                    user_name: appData.user.name,
                    amount: 1000
                })
            });
            const result = await res.json();
            if (result.success) {
                hien_thong_bao((currentLang === 'en' ? 'Deposit successful' : 'Nạp thành công') + ' +' + dinh_dang_tien_vnd(result.amount) + '!');
                await dong_bo_thong_tin_nguoi_dung();
                await dong_bo_du_lieu_cua_hang();
                lam_moi_toan_bo_giao_dien();
            } else if (result.manual_mode) {
                hien_thong_bao(result.message || (currentLang === 'en' ? 'Admin will manually approve your deposit.' : 'Admin sẽ duyệt nạp tiền thủ công cho bạn.'));
                dung_kiem_tra_nap_tien();
                setTimeout(() => {
                    if (activeTab === 'nap-tien') bat_dau_kiem_tra_nap_tien();
                }, 60000);
            }
        } catch (e) {}
    }, 5000);
}

async function dong_bo_du_lieu_cua_hang() {
    try {
        const res = await fetch('/api/shop-data');
        const data = await res.json();
        if (data) {
            appData.shopInfo = data.shopInfo || appData.shopInfo;
            appData.bankApi = data.bankApi || appData.bankApi;
            appData.categories = Array.isArray(data.categories) ? data.categories : [];
            appData.products = Array.isArray(data.products) ? data.products : [];
            appData.recentTransactions = data.recentTransactions || [];
            appData.topDepositors = data.topDepositors || [];
            if (data.musicUrl) {
                appData.musicUrl = data.musicUrl;
                thiet_lap_nhac_nen(data.musicUrl);
            }
        }
    } catch (e) {
        console.error(e);
    }
}

async function dong_bo_thong_tin_nguoi_dung() {
    try {
        const isPreview = (new URLSearchParams(window.location.search)).get('preview') === '1';
        const url = isPreview ? `/api/user-profile?preview=1&uid=${encodeURIComponent(appData.user.id)}` : '/api/user-profile';
        const res = await fetch(url, {
            headers: lay_header_bao_mat()
        });
        const data = await res.json();
        if (data) {
            appData.user.balance = data.balance || 0;
            appData.user.spent = data.spent || 0;
            appData.user.totalDeposit = data.totalDeposit || 0;
            appData.user.role = data.role || "customer";
            appData.user.inventory = data.inventory || [];
            appData.user.depositHistory = data.depositHistory || [];
        }
    } catch (e) {
        console.error(e);
    }
}

function chay_thanh_tien_trinh_tai(onComplete) {
    const bar = document.getElementById('splashProgressBar');
    const txt = document.getElementById('splashProgressText');
    const statusTxt = document.getElementById('splashStatusText');
    const splash = document.getElementById('splashScreen');
    let p = 5;
    const steps = [
        { threshold: 30, label: currentLang === 'en' ? "Connecting to Telegram..." : "Đang kết nối Telegram..." },
        { threshold: 65, label: currentLang === 'en' ? "Synchronizing balance..." : "Đang đồng bộ hồ sơ & số dư..." },
        { threshold: 90, label: currentLang === 'en' ? "Activating VietQR 24/7..." : "Kích hoạt cổng VietQR 24/7..." },
        { threshold: 100, label: currentLang === 'en' ? "Ready!" : "Khởi tạo thành công!" }
    ];
    const timer = setInterval(() => {
        p += Math.floor(Math.random() * 6) + 4;
        if (p > 100) p = 100;
        if (bar) bar.style.width = p + '%';
        if (txt) txt.innerText = p + '%';
        const step = steps.find(s => p <= s.threshold);
        if (step && statusTxt) statusTxt.innerText = step.label;
        if (p >= 100) {
            clearInterval(timer);
            setTimeout(() => {
                if (splash) {
                    splash.style.opacity = '0';
                    splash.style.transition = 'opacity 0.35s ease';
                    setTimeout(() => splash.remove(), 350);
                }
                if (onComplete) onComplete();
            }, 200);
        }
    }, 50);
}

window.addEventListener('DOMContentLoaded', async () => {
    const isMobile = bat_buoc_truy_cap_dien_thoai();
    if (!isMobile) return;
    dat_ngon_ngu(currentLang);
    const urlParams = new URLSearchParams(window.location.search);
    const isPreview = urlParams.get('preview') === '1' || urlParams.get('admin') === '1';

    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        const tgUser = window.Telegram.WebApp.initDataUnsafe?.user;
        if (tgUser) {
            appData.user.id = tgUser.id.toString();
            appData.user.name = tgUser.first_name || "Khách hàng";
            if (tgUser.photo_url) appData.user.avatar = tgUser.photo_url;
        }
    }
    if ((!appData.user.id || appData.user.id === "0") && isPreview) {
        const uidParam = urlParams.get('uid');
        const nameParam = urlParams.get('name');
        const avatarParam = urlParams.get('avatar');
        if (uidParam) appData.user.id = uidParam;
        if (nameParam) appData.user.name = decodeURIComponent(nameParam);
        if (avatarParam) appData.user.avatar = decodeURIComponent(avatarParam);
    }
    if (window.location.search && window.history && window.history.replaceState) {
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    hien_thi_thong_tin_nguoi_dung();
    chay_thanh_tien_trinh_tai(async () => {
        const isSecure = await kiem_tra_bao_mat_client();
        if (!isSecure) return;
        await dong_bo_du_lieu_cua_hang();
        await dong_bo_thong_tin_nguoi_dung();
        lam_moi_toan_bo_giao_dien();
        thong_bao_hoat_dong_admin('open_app');
        thu_tu_dong_phat_nhac();
    });
});
