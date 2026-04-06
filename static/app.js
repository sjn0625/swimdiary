const state = {
  me: null,
  options: null,
  profileId: null,
  planId: null,
  planData: null,
  progressData: null,
  currentStep: 1,
  userGroup: '爱好者',
  entitlements: {}
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || '请求失败');
  return data;
}

function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = `${isError ? '⚠️ ' : '✅ '}${message}`;
  toast.style.borderColor = isError ? 'rgba(255,124,133,.35)' : 'rgba(85,196,255,.35)';
  toast.classList.add('show');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => toast.classList.remove('show'), 2500);
}

function featureEnabled(code) {
  return !!state.entitlements?.[code];
}

function bindSelectOptions(id, values, mapper) {
  const select = document.getElementById(id);
  if (!select) return;
  select.innerHTML = values.map(item => {
    if (typeof item === 'object') {
      return `<option value="${item.value}">${item.label}</option>`;
    }
    return `<option value="${mapper ? mapper(item) : item}">${item}</option>`;
  }).join('');
}

function setStep(step) {
  state.currentStep = step;
  $$('.step-panel').forEach(panel => panel.classList.toggle('active', Number(panel.dataset.step) === step));
  $$('.step-chip').forEach(chip => chip.classList.toggle('active', Number(chip.dataset.stepIndex) === step));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderStepper() {
  const labels = ['选择群体', '建档与 CSS', '查看结果'];
  $('#stepper').innerHTML = labels.map((label, idx) => `<span class="step-chip ${idx + 1 === state.currentStep ? 'active' : ''}" data-step-index="${idx + 1}">${idx + 1}. ${label}</span>`).join('');
}

function collectProfileForm() {
  return {
    user_group: state.userGroup,
    display_name: $('#display_name').value.trim(),
    goal: $('#goal').value,
    level: $('#level').value,
    plan_scope: $('#plan_scope').value,
    cycle_length: $('#cycle_length').value,
    sessions_per_week: $('#sessions_per_week').value,
    session_duration: $('#session_duration').value,
    primary_stroke: $('#primary_stroke').value.trim(),
    discomfort: $('#discomfort').value.trim(),
    recent_result_flag: $('#recent_result_flag').value,
    best_result_distance: $('#best_result_distance').value.trim(),
    best_result_time: $('#best_result_time').value.trim(),
    watch_data_flag: $('#watch_data_flag').value,
    extra_note: $('#extra_note').value.trim(),
    sex: $('#sex').value,
    age: $('#age').value,
    height_cm: $('#height_cm').value,
    weight_kg: $('#weight_kg').value,
    body_fat: $('#body_fat').value,
    activity_level: $('#activity_level').value,
    css_400: $('#css_400').value.trim(),
    css_200: $('#css_200').value.trim(),
  };
}

function mountUserGroups() {
  const groups = {
    '爱好者': {
      desc: '默认用更通俗的语言表达计划，重点是这周怎么练。',
      benefits: ['周计划优先', '术语折叠显示', '先提高完成率再加复杂度']
    },
    '进阶训练者': {
      desc: '适合有规律训练基础、希望更清楚配速和强度结构的用户。',
      benefits: ['CSS 与 EN 区间结合', '滚动周计划更适合持续进步', '更明确的主刺激与恢复课逻辑']
    },
    '备赛用户': {
      desc: '完整展示 A / EN / SP 分区与周期节奏，适合比赛导向用户。',
      benefits: ['支持 4/6/8 周周期', '专项质量课与恢复逻辑更完整', '更适合比赛前准备']
    },
    '减脂用户': {
      desc: '训练与热量、饮食和缺口可视化联动，表达更生活化。',
      benefits: ['周计划优先', '热量估计与饮食建议', '重点看完成率与节奏可持续']
    }
  };
  $('#userGroupGrid').innerHTML = Object.entries(groups).map(([name, val]) => `
    <button class="user-type-card ${name === state.userGroup ? 'active' : ''}" data-user-group="${name}">
      <strong>${name}</strong>
      <span>${val.desc}</span>
    </button>`).join('');
  $('#groupExplanation').textContent = groups[state.userGroup].desc;
  $('#groupBenefits').innerHTML = groups[state.userGroup].benefits.map(x => `<li>${x}</li>`).join('');
  $$('.user-type-card').forEach(card => card.addEventListener('click', () => {
    state.userGroup = card.dataset.userGroup;
    mountUserGroups();
    autoAdjustByGroup();
  }));
}

function autoAdjustByGroup() {
  if (state.userGroup === '减脂用户') $('#goal').value = '减脂';
  if (state.userGroup === '备赛用户' && $('#goal').value === '减脂') $('#goal').value = '备赛';
  if (state.userGroup === '爱好者' && $('#plan_scope').value === 'cycle') $('#plan_scope').value = 'week';
}

async function initOptions() {
  state.options = await fetchJSON('/api/options');
  bindSelectOptions('goal', state.options.goals);
  bindSelectOptions('level', state.options.levels);
  bindSelectOptions('plan_scope', state.options.plan_scopes);
  bindSelectOptions('cycle_length', state.options.cycle_lengths, v => v);
  bindSelectOptions('activity_level', state.options.activity_levels);
  bindSelectOptions('completion_status', state.options.completion_status);
  bindSelectOptions('sleep_status', state.options.sleep_status);
  bindSelectOptions('discomfort_feedback', state.options.discomfort_feedback);
  autoAdjustByGroup();
}

async function refreshMe() {
  state.me = await fetchJSON('/api/me');
  const ent = await fetchJSON('/api/me/entitlements').catch(() => ({ tier: state.me.user.membership_tier || 'free', features: {} }));
  state.entitlements = ent.features || {};
  const user = state.me.user;
  $('#drawerUserInfo').innerHTML = `当前身份：<strong>${user.is_guest ? '访客模式' : '正式账号'}</strong><br>昵称：${user.nickname || '未设置'}<br>会员：${user.membership_tier === 'vip' ? 'VIP 成长版' : '免费版'}${user.email ? `<br>邮箱：${user.email}` : ''}`;
  renderAccountCard();
}

function ensurePlannerVisible() {
  $('#plannerSection').classList.remove('hidden');
  window.scrollTo({ top: $('#plannerSection').offsetTop - 60, behavior: 'smooth' });
}

async function calculateCss() {
  try {
    const result = await fetchJSON('/api/css/compute', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ css_400: $('#css_400').value, css_200: $('#css_200').value })
    });
    const color = result.valid ? 'var(--green)' : (result.kind === 'format' || result.kind === 'logic' ? 'var(--red)' : 'var(--muted)');
    $('#cssMessage').style.color = color;
    $('#cssMessage').textContent = result.message;
  } catch (err) {
    showToast(err.message, true);
  }
}

async function saveProfile(withToast = true) {
  const result = await fetchJSON('/api/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(collectProfileForm())
  });
  state.profileId = result.profile_id;
  $('#cssMessage').style.color = 'var(--green)';
  $('#cssMessage').textContent = result.css_info?.message || '建档已保存。';
  if (withToast) showToast('建档已保存。');
  return result;
}

function renderPlanSummary(plan) {
  $('#planEmptyState').classList.add('hidden');
  $('#planResultBody').classList.remove('hidden');
  $('#planSummaryText').innerHTML = `
    <div class="muted">${plan.summary}</div>
    <div style="margin-top:10px">${plan.headline}</div>
  `;
  $('#planMetaPills').innerHTML = `
    <span class="pill">${plan.plan_scope === 'week' ? '周计划' : '周期计划'}</span>
    <span class="pill">${plan.data_precision}</span>
    <span class="pill">用户群体：${state.userGroup}</span>
  `;
}

function renderWeeklyPlan(plan) {
  $('#weeklyPlanCard').innerHTML = `
    <div class="section-title">本周训练安排</div>
    ${plan.weekly_plan.map((session, idx) => `
      <article class="session-card">
        <div class="legend-row"><h3>${session.title}</h3><span class="pill">第 ${idx + 1} 次</span></div>
        <div class="muted">${session.intention}</div>
        <div class="legend-row" style="margin-top:10px"><strong>预计总量</strong><span>${session.total_distance}</span></div>
        <div class="muted" style="margin-top:8px">${session.effort_explainer}</div>
        <div class="segment-list" style="margin-top:10px">
          ${session.segments.map(seg => `
            <div class="segment-item">
              <div class="segment-meta">${seg.label}｜${seg.zone}</div>
              <div>${seg.detail}</div>
            </div>`).join('')}
        </div>
        <ul class="note-list" style="margin-top:10px">${session.notes.map(note => `<li>${note}</li>`).join('')}</ul>
      </article>`).join('')}
  `;
  $('#session_index').innerHTML = plan.weekly_plan.map((session, idx) => `<option value="${idx}">${session.title}</option>`).join('');
  const first = plan.weekly_plan[0];
  $('#todayCard').innerHTML = `
    <div class="section-title">今日训练 / 移动端执行模式</div>
    <div class="muted">大多数用户最常用的是“今天练什么”，不是一整张长表。</div>
    <article class="session-card">
      <div class="legend-row"><strong>${first.title}</strong><span class="pill">建议优先完成</span></div>
      <div class="muted" style="margin-top:8px">${first.intention}</div>
      <div class="segment-list" style="margin-top:12px">
        ${first.segments.map(seg => `<div class="segment-item"><div class="segment-meta">${seg.label}</div><div>${seg.detail}</div></div>`).join('')}
      </div>
      <div class="step-actions compact" style="margin-top:12px"><button class="primary-btn" data-tab-target="feedback">练完去反馈</button></div>
    </article>`;
  $$('[data-tab-target="feedback"]').forEach(btn => btn.addEventListener('click', () => switchDashboardTab('feedback')));
}

function renderDistribution(plan) {
  $('#distributionCard').innerHTML = `
    <div class="section-title">强度分布与安排逻辑</div>
    <div class="bar-stack">
      ${Object.entries(plan.zone_distribution).map(([key, val]) => `
        <div class="bar-row">
          <div class="legend-row"><span>${key}</span><strong>${val}%</strong></div>
          <div class="bar-track"><div class="bar-fill" style="width:${val}%"></div></div>
        </div>`).join('')}
    </div>
    <ul class="note-list" style="margin-top:10px">${plan.coach_notes.map(x => `<li>${x}</li>`).join('')}</ul>
    ${plan.warnings?.length ? `<div class="inline-notice" style="margin-top:12px">${plan.warnings.join('<br>')}</div>` : ''}
  `;
}

function renderGuide(plan) {
  $('#guideCard').innerHTML = `
    <div class="section-title">强度区间说明</div>
    <div class="zone-grid">
      ${plan.intensity_guide.map(item => `
        <div class="zone-item">
          <div class="zone-head"><span>${item.code}｜${item.name}</span><span class="zone-range">${item.pace_range}</span></div>
          <div class="muted" style="margin-top:8px">${item.description}</div>
        </div>`).join('')}
    </div>
  `;
}

function renderCycle(plan) {
  if (!plan.cycle_overview) {
    $('#cycleCard').innerHTML = `
      <div class="section-title">周期总览</div>
      <div class="muted">当前为周计划模式。对于大多数用户，默认先看本周计划和训练完成率，更容易长期坚持。</div>`;
    return;
  }
  $('#cycleCard').innerHTML = `
    <div class="section-title">周期总览</div>
    ${plan.cycle_overview.map(week => `
      <article class="week-card">
        <div class="legend-row"><strong>${week.title}</strong><span>${week.theme}</span></div>
        <div class="muted" style="margin-top:8px">${week.focus}</div>
        <div class="pill-row" style="margin-top:10px"><span class="pill">负荷：${week.load_hint}</span><span class="pill">关键课：${week.key_session}</span></div>
      </article>`).join('')}
  `;
}

function renderNutrition(plan) {
  if (!plan.nutrition || !plan.calories) {
    $('#nutritionCard').innerHTML = `
      <div class="section-title">减脂与饮食联动</div>
      <div class="muted">当前用户不是减脂路径，或缺少足够身体信息，因此这里只保留扩展位。</div>`;
    return;
  }
  const macros = plan.nutrition.macros || { protein_pct: 30, carb_pct: 40, fat_pct: 30 };
  const protein = macros.protein_pct || 30;
  const carb = Math.min(100, protein + (macros.carb_pct || 40));
  const cal = plan.calories;
  const maxVal = Math.max(cal.maintenance_kcal || 1, cal.training_day_target_kcal || 1, cal.target_deficit_kcal || 1);
  $('#nutritionCard').innerHTML = `
    <div class="section-title">减脂、热量与饮食联动</div>
    <div class="muted">热量缺口更适合用对比和趋势展示，因此这里用条形图看维持热量、建议摄入和目标缺口；宏量营养素才用饼状表现。</div>
    <div class="bar-stack" style="margin-top:12px">
      ${[['维持热量', cal.maintenance_kcal], ['训练日建议摄入', cal.training_day_target_kcal], ['目标缺口', cal.target_deficit_kcal]].map(([label, value]) => `
        <div class="bar-row">
          <div class="legend-row"><span>${label}</span><strong>${value ? `${value} kcal` : '待补充'}</strong></div>
          <div class="bar-track"><div class="bar-fill" style="width:${value ? value / maxVal * 100 : 0}%"></div></div>
        </div>`).join('')}
    </div>
    <div class="donut-wrap" style="margin-top:14px">
      <div class="donut" style="--protein:${protein}%; --carb:${carb}%"></div>
      <div class="donut-labels">
        <div class="dotline"><span class="dot protein"></span><span>蛋白 ${macros.protein_g || '-'}g</span></div>
        <div class="dotline"><span class="dot carb"></span><span>碳水 ${macros.carb_g || '-'}g</span></div>
        <div class="dotline"><span class="dot fat"></span><span>脂肪 ${macros.fat_g || '-'}g</span></div>
      </div>
    </div>
    <ul class="note-list" style="margin-top:12px">
      ${plan.nutrition.meals.map(item => `<li>${item}</li>`).join('')}
      <li>${plan.calories.note}</li>
    </ul>
  `;
}

function renderPlan(plan) {
  state.planData = plan;
  renderPlanSummary(plan);
  renderWeeklyPlan(plan);
  renderDistribution(plan);
  renderGuide(plan);
  renderCycle(plan);
  renderNutrition(plan);
  $('#dashboardSection').classList.remove('hidden');
}

async function generatePlan() {
  try {
    if (!state.profileId) await saveProfile(false);
    const data = await fetchJSON('/api/plan/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_id: state.profileId })
    });
    state.planId = data.plan_id;
    renderPlan(data);
    setStep(3);
    showToast('计划已生成。');
    await loadProgress();
  } catch (err) {
    showToast(err.message, true);
  }
}

function renderPricing() {
  const tier = state.me?.user?.membership_tier || 'free';
  const features = state.entitlements || {};
  const locked = [
    ['滚动周计划', features.rollover_week],
    ['完整成长看板', features.progress_trends_full],
    ['Word / PDF 导出', features.exports],
    ['进阶周期计划', features.cycle_plan],
    ['高级营养联动', features.nutrition_advanced],
  ];
  $('#pricingCard').innerHTML = `
    <div class="section-title">免费版 vs VIP 成长版</div>
    <div class="grid gap-lg">
      <article class="session-card">
        <div class="legend-row"><strong>免费版</strong><span class="pill">先体验价值</span></div>
        <ul class="note-list" style="margin-top:10px">${state.options.pricing.free.map(x => `<li>${x}</li>`).join('')}</ul>
        <div class="inline-notice" style="margin-top:10px">免费版重点是让用户先拿到周计划并形成反馈习惯。</div>
      </article>
      <article class="session-card">
        <div class="legend-row"><strong>VIP 成长版</strong><span class="pill">${tier === 'vip' ? '已激活' : '推荐升级'}</span></div>
        <ul class="note-list" style="margin-top:10px">${state.options.pricing.vip.map(x => `<li>${x}</li>`).join('')}</ul>
        <div class="pill-row" style="margin-top:10px">${locked.map(([label, ok]) => `<span class="pill">${ok ? '✅' : '🔒'} ${label}</span>`).join('')}</div>
        <div class="step-actions compact" style="margin-top:12px">
          <button class="primary-btn" id="vipMonthlyBtn">网页支付月卡</button>
          <button class="secondary-btn" id="vipYearlyBtn">网页支付年卡</button>
          <button class="ghost-btn" id="devVipBtn">开发环境体验 VIP</button>
        </div>
      </article>
    </div>
  `;
  $('#vipMonthlyBtn')?.addEventListener('click', () => checkout('monthly'));
  $('#vipYearlyBtn')?.addEventListener('click', () => checkout('yearly'));
  $('#devVipBtn')?.addEventListener('click', async () => {
    try {
      const data = await fetchJSON('/api/membership/dev-upgrade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tier: tier === 'vip' ? 'free' : 'vip' }) });
      await refreshMe();
      renderPricing();
      showToast(`当前会员已切换为 ${data.membership_tier.toUpperCase()}`);
    } catch (err) {
      showToast(err.message, true);
    }
  });
}

function renderAccountCard() {
  const user = state.me?.user || {};
  const stageText = featureEnabled('progress_trends_full') ? '你可以查看完整成长趋势，并按周滚动更新计划。' : '当前可先体验计划与基础反馈，完整成长跟踪为 VIP 功能。';
  $('#accountCard').innerHTML = `
    <div class="section-title">账户与成长状态</div>
    <div class="muted">${user.is_guest ? '当前是访客模式，仍可直接体验，但历史只保留在当前设备会话中。建议注册账号把历史计划、反馈和会员权益长期保存。' : '当前为正式账号，可以跨设备同步计划、反馈和会员状态。'}</div>
    <div class="pill-row" style="margin-top:12px">
      <span class="pill">昵称：${user.nickname || '未设置'}</span>
      <span class="pill">会员：${user.membership_tier === 'vip' ? 'VIP 成长版' : '免费版'}</span>
      ${user.email ? `<span class="pill">${user.email}</span>` : ''}
    </div>
    <div class="inline-notice" style="margin-top:12px">${stageText}</div>
    <div class="step-actions compact" style="margin-top:12px">
      <button class="secondary-btn" id="openDrawerBtn2">管理账户</button>
    </div>`;
  $('#openDrawerBtn2')?.addEventListener('click', openDrawer);
}

async function checkout(plan) {
  try {
    const data = await fetchJSON('/api/billing/web/checkout-session', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan })
    });
    window.location.href = data.url;
  } catch (err) {
    showToast(err.message, true);
  }
}

function renderTrendChart(progress) {
  const labels = progress.charts?.labels || [];
  const completion = progress.charts?.completion || [];
  const fatigue = progress.charts?.fatigue || [];
  const distance = progress.charts?.distance || [];
  if (!completion.length && !fatigue.length && !distance.length) {
    $('#trendChartWrap').innerHTML = `<div class="muted">还没有足够的反馈数据。连续反馈后，这里会出现完成率、疲劳与训练距离趋势。</div>`;
    return;
  }
  const width = 560;
  const height = 220;
  const pad = 28;
  const count = Math.max(labels.length, completion.length, fatigue.length, distance.length, 1);
  const step = (width - pad * 2) / Math.max(count - 1, 1);
  const maxDistance = Math.max(...distance, 1);
  const maxFatigue = 10;
  const makeLine = (arr, maxVal, offset = 0) => arr.map((v, i) => `${pad + i * step},${height - pad - ((v + offset) / maxVal) * (height - pad * 2)}`).join(' ');
  const bars = distance.map((v, i) => {
    const x = pad + i * step - 10;
    const barH = ((v || 0) / maxDistance) * 56;
    return `<rect x="${x}" y="${height - pad - barH}" width="20" height="${barH}" rx="8" fill="rgba(125,255,175,.35)" />`;
  }).join('');
  const xLabels = labels.map((label, i) => `<text x="${pad + i * step}" y="${height - 6}" fill="rgba(222,238,255,.6)" font-size="11" text-anchor="middle">${label}</text>`).join('');
  $('#trendChartWrap').innerHTML = `
    <svg class="trend-svg" viewBox="0 0 ${width} ${height}">
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(255,255,255,.12)" />
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(255,255,255,.12)" />
      ${bars}
      ${completion.length ? `<polyline fill="none" stroke="#55c4ff" stroke-width="3" points="${makeLine(completion, 100)}" />` : ''}
      ${fatigue.length ? `<polyline fill="none" stroke="#ffb457" stroke-width="3" points="${makeLine(fatigue.map(v => v * 10), 100)}" />` : ''}
      ${xLabels}
    </svg>
    <div class="trend-legend"><span>蓝线：完成率</span><span>橙线：疲劳</span><span>绿色柱：实际距离</span></div>
  `;
}

function renderProgress(progress) {
  state.progressData = progress;
  const overview = progress.overview;
  $('#progressStats').innerHTML = [
    ['成长指数', overview.growth_score],
    ['连续性', `${overview.consistency_score}%`],
    ['恢复分', `${overview.recovery_score}%`],
    ['当前状态', overview.current_status],
  ].map(([label, value]) => `<article class="stat-card glass"><span>${label}</span><strong>${value}</strong><span>${label === '当前状态' ? `动量：${overview.momentum_label}` : `阶段：${overview.stage?.title || '-'}`}</span></article>`).join('');
  renderTrendChart(progress);
  $('#feedbackHistoryList').innerHTML = progress.feedback_history.length ? progress.feedback_history.slice(-8).reverse().map(item => `
    <article class="timeline-item">
      <div class="timeline-head"><span>${item.created_at}</span><span>${item.completion_ratio}%</span></div>
      <strong>${item.judgment || '训练反馈'}</strong>
      <div class="muted">完成度：${item.completion_status}｜疲劳：${item.fatigue_score}｜睡眠：${item.sleep_status}</div>
      <div class="muted">${item.direction || ''}</div>
    </article>`).join('') : `<div class="muted">暂无反馈记录。</div>`;
  $('#historyCard').innerHTML = `
    <div class="section-title">历史计划与导出</div>
    <div class="timeline-list">
      ${progress.plan_history.length ? progress.plan_history.slice(0, 6).map(plan => `
        <article class="timeline-item">
          <div class="timeline-head"><span>${plan.created_at}</span><span>V${plan.plan_version}</span></div>
          <strong>${plan.plan_scope === 'week' ? '周计划' : '周期计划'}</strong>
          <div class="muted">${plan.summary}</div>
        </article>`).join('') : '<div class="muted">还没有历史计划。</div>'}
    </div>`;
  $('#growthJourneyCard').innerHTML = `
    <div class="section-title">成长阶段与里程碑</div>
    <div class="inline-notice">${overview.stage?.title || '建立节奏期'}｜${overview.stage?.description || ''}</div>
    <div class="pill-row" style="margin-top:12px">
      <span class="pill">最佳连续反馈：${overview.best_streak || 0} 次</span>
      <span class="pill">动量：${overview.momentum_label}</span>
      <span class="pill">CSS 参考：${overview.latest_css_hint || '未接入'}</span>
    </div>
    <ul class="note-list" style="margin-top:12px">${(progress.milestones?.length ? progress.milestones : ['继续完成反馈，逐步建立自己的成长曲线。']).map(item => `<li>${item}</li>`).join('')}</ul>
  `;
  $('#rolloverInsightCard').innerHTML = `
    <div class="section-title">下周滚动建议</div>
    <div class="muted">${overview.next_focus}</div>
    <div class="pill-row" style="margin-top:12px">
      <span class="pill">${featureEnabled('rollover_week') ? '可自动生成下周' : '升级后可自动滚动生成'}</span>
      <span class="pill">当前计划：${overview.latest_plan_scope === 'cycle' ? '周期计划' : '周计划'}</span>
    </div>
    ${progress.calorie_overview ? `<div class="inline-notice" style="margin-top:12px">减脂目标：训练日建议约 ${progress.calorie_overview.training_day_target_kcal || '-'} kcal；目标缺口 ${progress.calorie_overview.target_deficit_kcal || '-'} kcal。</div>` : ''}
    <div class="step-actions compact" style="margin-top:12px">
      <button class="primary-btn" id="rolloverPlanBtn2">生成下一周滚动计划</button>
    </div>
  `;
  $('#rolloverPlanBtn2')?.addEventListener('click', generateRolloverPlan);
}

async function loadProgress() {
  try {
    const progress = await fetchJSON('/api/progress/overview');
    renderProgress(progress);
  } catch (err) {
    console.error(err);
  }
}

function switchDashboardTab(tab) {
  $$('.tab-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
  $$('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.dataset.tabPanel === tab));
}

function openDrawer() { $('#accountDrawer').classList.remove('hidden'); }
function closeDrawer() { $('#accountDrawer').classList.add('hidden'); }

async function initExistingState() {
  const profileRes = await fetchJSON('/api/profile/latest');
  if (profileRes.profile) {
    state.profileId = profileRes.profile.id;
    fillProfileForm(profileRes.profile);
  }
  const currentRes = await fetchJSON('/api/plan/current');
  if (currentRes.plan_id) {
    state.planId = currentRes.plan_id;
    renderPlan(currentRes);
    $('#plannerSection').classList.remove('hidden');
    $('#dashboardSection').classList.remove('hidden');
  }
  await loadProgress();
}

function fillProfileForm(profile) {
  state.userGroup = profile.user_group || state.userGroup;
  mountUserGroups();
  const map = {
    display_name: profile.display_name,
    goal: profile.goal,
    level: profile.level,
    plan_scope: profile.plan_scope,
    cycle_length: profile.cycle_length,
    sessions_per_week: profile.sessions_per_week,
    session_duration: profile.session_duration,
    primary_stroke: profile.primary_stroke,
    discomfort: profile.discomfort,
    recent_result_flag: profile.recent_result_flag,
    best_result_distance: profile.best_result_distance,
    best_result_time: profile.best_result_time,
    watch_data_flag: profile.watch_data_flag,
    extra_note: profile.extra_note,
    sex: profile.sex,
    age: profile.age,
    height_cm: profile.height_cm,
    weight_kg: profile.weight_kg,
    body_fat: profile.body_fat,
    activity_level: profile.activity_level,
    css_400: profile.css_400,
    css_200: profile.css_200,
  };
  Object.entries(map).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el && value !== null && value !== undefined) el.value = value;
  });
}

async function generateRolloverPlan() {
  try {
    const data = await fetchJSON('/api/plan/rollover', { method: 'POST' });
    state.planId = data.plan_id;
    renderPlan(data);
    $('#dashboardSection').classList.remove('hidden');
    switchDashboardTab('today');
    await loadProgress();
    showToast(data.message || '已生成下一周滚动计划。');
  } catch (err) {
    showToast(err.message, true);
    if ((err.message || '').includes('VIP')) {
      switchDashboardTab('membership');
    }
  }
}

async function submitFeedback(e) {
  e.preventDefault();
  if (!state.planId) return showToast('请先生成计划。', true);
  const form = new FormData();
  form.append('plan_id', state.planId);
  form.append('session_index', $('#session_index').value || 0);
  form.append('completion_status', $('#completion_status').value);
  form.append('fatigue_score', $('#fatigue_score').value);
  form.append('sleep_status', $('#sleep_status').value);
  form.append('discomfort_feedback', $('#discomfort_feedback').value);
  form.append('feedback_note', $('#feedback_note').value.trim());
  form.append('actual_distance_m', $('#actual_distance_m').value);
  form.append('actual_duration_s', $('#actual_duration_s').value);
  form.append('avg_pace_per_100_s', $('#avg_pace_per_100_s').value);
  form.append('avg_hr', $('#avg_hr').value);
  form.append('ocr_text', $('#ocr_text').value.trim());
  const file = $('#screenshot').files[0];
  if (file) form.append('screenshot', file);
  try {
    const result = await fetchJSON('/api/feedback', { method: 'POST', body: form });
    $('#feedbackResultCard').innerHTML = `
      <div class="section-title">系统判断</div>
      <div class="inline-notice">${result.judgment}</div>
      <div class="muted" style="margin-top:10px">${result.direction}</div>
      <div class="pill-row" style="margin-top:12px"><span class="pill">建议强度：${result.recommended_zone}</span><span class="pill">下周动作：${result.next_week_action}</span><span class="pill">完成判定：${result.adherence_label}</span></div>
      <article class="session-card" style="margin-top:12px">
        <div class="legend-row"><strong>下一次训练建议</strong><span class="pill">${result.next_week_action}</span></div>
        <ul class="note-list" style="margin-top:10px">
          <li><strong>目标：</strong>${result.next_session.goal}</li>
          <li><strong>热身：</strong>${result.next_session.warmup}</li>
          <li><strong>主训练：</strong>${result.next_session.main}</li>
          <li><strong>放松：</strong>${result.next_session.cooldown}</li>
          <li><strong>备注：</strong>${result.next_session.note}</li>
        </ul>
      </article>
      ${result.watch_analysis?.planned_distance_range ? `<div class="muted" style="margin-top:12px">计划距离：${result.watch_analysis.planned_distance_range[0]}-${result.watch_analysis.planned_distance_range[1]}m；实际距离：${result.watch_analysis.actual_distance_m || '-'}m</div>` : ''}
    `;
    if (result.progress) {
      await loadProgress();
    }
    switchDashboardTab('feedback');
    showToast('反馈已记录，并已生成下次建议。');
    $('#feedbackForm').reset();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function downloadFile(type) {
  if (!state.planId) return showToast('请先生成计划。', true);
  window.location.href = `/api/export/${type}/${state.planId}`;
}

function bindGlobalNavigation() {
  $('#startPlannerBtn').addEventListener('click', () => {
    ensurePlannerVisible();
    setStep(1);
  });
  $('#jumpMembershipBtn').addEventListener('click', () => {
    $('#dashboardSection').classList.remove('hidden');
    switchDashboardTab('membership');
    document.querySelector('[data-tab-panel="membership"]').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  $('#openTodayBtn').addEventListener('click', () => {
    $('#dashboardSection').classList.remove('hidden');
    switchDashboardTab('today');
    $('#dashboardSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  $('.bottom-nav').addEventListener('click', (e) => {
    const btn = e.target.closest('.nav-btn');
    if (!btn) return;
    const target = btn.dataset.go;
    $$('.nav-btn').forEach(x => x.classList.toggle('active', x === btn));
    if (target === 'hero') window.scrollTo({ top: 0, behavior: 'smooth' });
    if (target === 'planner') { ensurePlannerVisible(); }
    if (['today','feedback','membership'].includes(target)) {
      $('#dashboardSection').classList.remove('hidden');
      switchDashboardTab(target === 'membership' ? 'membership' : target);
      $('#dashboardSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
  $$('.tab-btn').forEach(btn => btn.addEventListener('click', () => switchDashboardTab(btn.dataset.tab)));
  $$('[data-next-step]').forEach(btn => btn.addEventListener('click', () => { setStep(Number(btn.dataset.nextStep)); renderStepper(); }));
  $$('[data-prev-step]').forEach(btn => btn.addEventListener('click', () => { setStep(Number(btn.dataset.prevStep)); renderStepper(); }));
}

function bindAccountDrawer() {
  $('#accountBtn').addEventListener('click', openDrawer);
  $('#closeDrawerBtn').addEventListener('click', closeDrawer);
  $('#drawerBackdrop').addEventListener('click', closeDrawer);
  $('#registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const data = await fetchJSON('/api/auth/register', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nickname: $('#register_nickname').value.trim(),
          email: $('#register_email').value.trim(),
          password: $('#register_password').value
        })
      });
      await refreshMe();
      renderPricing();
      showToast(data.message);
      closeDrawer();
      $('#registerForm').reset();
    } catch (err) {
      showToast(err.message, true);
    }
  });
  $('#loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const data = await fetchJSON('/api/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: $('#login_email').value.trim(), password: $('#login_password').value })
      });
      await refreshMe();
      await initExistingState();
      renderPricing();
      showToast(data.message);
      closeDrawer();
      $('#loginForm').reset();
    } catch (err) {
      showToast(err.message, true);
    }
  });
  $('#logoutBtn').addEventListener('click', async () => {
    try {
      const data = await fetchJSON('/api/auth/logout', { method: 'POST' });
      await refreshMe();
      renderPricing();
      showToast(data.message);
      closeDrawer();
    } catch (err) {
      showToast(err.message, true);
    }
  });
}

function bindForms() {
  $('#cssCalcBtn').addEventListener('click', calculateCss);
  $('#saveProfileBtn').addEventListener('click', async () => {
    try {
      await saveProfile(true);
    } catch (err) {
      showToast(err.message, true);
    }
  });
  $('#generatePlanBtn').addEventListener('click', generatePlan);
  $('#feedbackForm').addEventListener('submit', submitFeedback);
  $('#exportDocBtn').addEventListener('click', () => downloadFile('docx'));
  $('#exportPdfBtn').addEventListener('click', () => downloadFile('pdf'));
  $('#rolloverPlanBtn')?.addEventListener('click', generateRolloverPlan);
}

async function init() {
  renderStepper();
  mountUserGroups();
  bindGlobalNavigation();
  bindAccountDrawer();
  bindForms();
  await initOptions();
  await refreshMe();
  renderPricing();
  await initExistingState();
  const params = new URLSearchParams(window.location.search);
  if (params.get('billing') === 'success') showToast('支付成功后请刷新会员状态，完整成长系统会自动解锁。');
  if ('serviceWorker' in navigator && !['127.0.0.1', 'localhost'].includes(location.hostname)) {
  navigator.serviceWorker.register('/service-worker.js').catch(() => {});
}
}

init().catch(err => {
  console.error(err);
  showToast('初始化失败，请检查控制台。', true);
});
