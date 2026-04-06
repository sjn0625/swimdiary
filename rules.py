import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ''
    return unicodedata.normalize('NFKC', str(value)).strip()


# ---------- CSS ----------

def parse_time_to_seconds(value: Optional[str]) -> Optional[float]:
    if value in [None, '']:
        return None
    text = normalize_text(value).replace(' ', '').replace('：', ':')
    if not text:
        return None
    if re.fullmatch(r'\d+(\.\d+)?', text):
        return float(text)
    match = re.fullmatch(r'(\d+):(\d{1,2})(?:\.(\d{1,2}))?', text)
    if not match:
        return None
    minute = int(match.group(1))
    second = int(match.group(2))
    centi = match.group(3)
    frac = float(f'0.{centi}') if centi else 0.0
    return minute * 60 + second + frac


def format_seconds_as_pace(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    total = float(value)
    minute = int(total // 60)
    second = total - minute * 60
    if abs(second - round(second)) < 1e-9:
        return f'{minute}:{int(round(second)):02d}/100m'
    return f'{minute}:{second:04.1f}/100m'


def format_range(low: Optional[float], high: Optional[float]) -> str:
    if low is None or high is None:
        return '按体感执行'
    return f'{format_seconds_as_pace(low)} – {format_seconds_as_pace(high)}'


def compute_css_from_inputs(css_400: Optional[str], css_200: Optional[str]) -> Dict:
    empty_400 = css_400 in [None, '']
    empty_200 = css_200 in [None, '']
    if empty_400 and empty_200:
        return {
            'valid': False,
            'kind': 'missing',
            'message': '未填写 CSS 计时，系统将按训练目标与体感生成计划。'
        }

    t400 = parse_time_to_seconds(css_400)
    t200 = parse_time_to_seconds(css_200)
    if t400 is None or t200 is None:
        return {
            'valid': False,
            'kind': 'format',
            'message': 'CSS 时间格式不正确，请输入如 4:30、4：30、4:30.5 或 270。'
        }
    if t400 <= t200:
        return {
            'valid': False,
            'kind': 'logic',
            'message': '400m 计时应大于 200m 计时，请检查输入。'
        }
    css_pace = (t400 - t200) / 2
    return {
        'valid': True,
        'kind': 'ok',
        'css_pace_seconds': css_pace,
        'css_pace_label': format_seconds_as_pace(css_pace),
        'message': f'CSS 已计算：{format_seconds_as_pace(css_pace)}。'
    }


# ---------- Training design ----------

def base_distance_by_level(level: str, duration: int) -> Tuple[int, int]:
    factor = {
        '零基础/恢复训练': 22,
        '爱好者': 28,
        '进阶爱好者': 34,
        '比赛/备赛': 40,
    }.get(level, 28)
    lower = max(600, int(duration * factor * 0.8))
    upper = max(lower + 300, int(duration * factor * 1.05))
    return lower, upper


def load_pattern_for_cycle(length: int) -> List[Tuple[str, str]]:
    if length <= 1:
        return [('执行周', '建立节奏')]
    if length == 4:
        return [
            ('第 1 周', '建立节奏'),
            ('第 2 周', '稳定推进'),
            ('第 3 周', '重点刺激'),
            ('第 4 周', '吸收与复盘'),
        ]
    if length == 6:
        return [
            ('第 1 周', '建立节奏'),
            ('第 2 周', '稳定推进'),
            ('第 3 周', '重点刺激'),
            ('第 4 周', '吸收与微调'),
            ('第 5 周', '第二轮推进'),
            ('第 6 周', '测试与复盘'),
        ]
    return [
        ('第 1 周', '建立节奏'),
        ('第 2 周', '基础推进'),
        ('第 3 周', '重点刺激'),
        ('第 4 周', '吸收调整'),
        ('第 5 周', '第二轮推进'),
        ('第 6 周', '专项强化'),
        ('第 7 周', '减量整合'),
        ('第 8 周', '测试与复盘'),
    ]


def get_intensity_guide(css_pace_seconds: Optional[float]) -> List[Dict]:
    guide = [
        {
            'code': 'A1',
            'name': '恢复 / 轻松有氧',
            'description': '热身、放松、恢复，强调轻松和动作放松。',
            'pace_range': format_range(css_pace_seconds + 20 if css_pace_seconds else None, css_pace_seconds + 35 if css_pace_seconds else None),
            'simple_label': '轻松游'
        },
        {
            'code': 'A2',
            'name': '基础有氧发展',
            'description': '稳定有氧、可持续输出，适合大部分爱好者的基础容量训练。',
            'pace_range': format_range(css_pace_seconds + 12 if css_pace_seconds else None, css_pace_seconds + 20 if css_pace_seconds else None),
            'simple_label': '稳定游'
        },
        {
            'code': 'EN1',
            'name': '基础耐力',
            'description': '阈值以下的主耐力区，用于建立总量和配速稳定性。',
            'pace_range': format_range(css_pace_seconds + 8 if css_pace_seconds else None, css_pace_seconds + 15 if css_pace_seconds else None),
            'simple_label': '有氧主训练'
        },
        {
            'code': 'EN2',
            'name': '阈值 / CSS 主训练',
            'description': '接近 CSS 的主训练区，提升持续输出和配速控制。',
            'pace_range': format_range(css_pace_seconds + 2 if css_pace_seconds else None, css_pace_seconds + 7 if css_pace_seconds else None),
            'simple_label': '较高强度稳定训练'
        },
        {
            'code': 'EN3',
            'name': '高强有氧 / VO2',
            'description': '高于 EN2 的持续刺激区，适合进阶用户和备赛用户。',
            'pace_range': format_range(css_pace_seconds - 3 if css_pace_seconds else None, css_pace_seconds + 1 if css_pace_seconds else None),
            'simple_label': '高强有氧'
        },
        {
            'code': 'SP1',
            'name': '速度耐受',
            'description': '短距离高强、休息中等，强调在困难状态下维持动作。',
            'pace_range': '按项目与休息比执行',
            'simple_label': '速度耐受'
        },
        {
            'code': 'SP2',
            'name': '无氧速度刺激',
            'description': '更短、更快、休息更充分，强调比赛速度和高质量输出。',
            'pace_range': '按项目与组长执行',
            'simple_label': '高速重复'
        },
        {
            'code': 'SP3',
            'name': '最大速度 / 爆发',
            'description': '超短距离、超高质量、充分休息，强调纯速度和神经招募。',
            'pace_range': '按最大速度执行',
            'simple_label': '爆发冲刺'
        },
    ]
    return guide


def user_copy_mode(user_group: str) -> str:
    if user_group == '爱好者':
        return 'simple'
    if user_group == '减脂用户':
        return 'fat_loss'
    if user_group == '备赛用户':
        return 'pro'
    return 'standard'


def zone_distribution(goal: str, user_group: str) -> Dict[str, int]:
    if user_group == '减脂用户':
        return {'A1/A2': 45, 'EN1': 35, 'EN2': 15, 'EN3/SP': 5}
    if goal == '提高速度':
        return {'A1/A2': 25, 'EN1': 25, 'EN2': 30, 'EN3/SP': 20}
    if goal == '备赛':
        return {'A1/A2': 20, 'EN1': 25, 'EN2': 35, 'EN3/SP': 20}
    if goal == '减脂':
        return {'A1/A2': 40, 'EN1': 35, 'EN2': 20, 'EN3/SP': 5}
    return {'A1/A2': 30, 'EN1': 40, 'EN2': 20, 'EN3/SP': 10}


def summarize_profile(profile: Dict) -> str:
    text = f"{profile['user_group']} · {profile['level']} · 目标：{profile['goal']}。每周 {profile['sessions_per_week']} 练，每次约 {profile['session_duration']} 分钟。"
    if profile.get('discomfort') and profile['discomfort'] != '没有明显不适':
        text += f" 当前需要注意：{profile['discomfort']}。"
    if profile.get('css_pace_seconds'):
        text += f" 已提供 CSS 参考：{format_seconds_as_pace(profile['css_pace_seconds'])}。"
    return text


@dataclass
class SessionSegment:
    label: str
    zone: str
    detail: str


@dataclass
class SessionPlan:
    title: str
    intention: str
    total_distance: str
    effort_explainer: str
    segments: List[SessionSegment]
    notes: List[str]

    def to_dict(self):
        data = asdict(self)
        data['segments'] = [asdict(s) for s in self.segments]
        return data


def session_label(zone: str, copy_mode: str) -> str:
    mapping = {
        'A1': ('轻松游', 'A1'),
        'A2': ('稳定游', 'A2'),
        'EN1': ('有氧主训练', 'EN1'),
        'EN2': ('阈值主训练', 'EN2'),
        'EN3': ('高强有氧', 'EN3'),
        'SP1': ('速度耐受', 'SP1'),
        'SP2': ('高速重复', 'SP2'),
        'SP3': ('爆发冲刺', 'SP3'),
    }
    simple, pro = mapping[zone]
    if copy_mode == 'simple':
        return f'{simple}（{pro}）'
    if copy_mode == 'fat_loss' and zone in {'A1', 'A2', 'EN1', 'EN2'}:
        fat = {
            'A1': '轻松恢复',
            'A2': '稳定燃脂',
            'EN1': '耐力燃脂',
            'EN2': '较高强度代谢刺激',
        }[zone]
        return f'{fat}（{pro}）'
    return pro


def build_session_templates(profile: Dict) -> List[SessionPlan]:
    sessions = int(profile['sessions_per_week'])
    duration = int(profile['session_duration'])
    lower, upper = base_distance_by_level(profile['level'], duration)
    user_group = profile['user_group']
    goal = profile['goal']
    copy_mode = user_copy_mode(user_group)
    base_total = f'{lower}–{upper} m'

    if user_group == '减脂用户':
        bank = [
            SessionPlan(
                title='第 1 次｜稳定执行日',
                intention='先把一节完整训练做下来，兼顾消耗与动作稳定。',
                total_distance=base_total,
                effort_explainer='以可持续完成为第一优先，主训练不过早冲强度。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '200–400m 轻松游 + 4×25m 技术激活'),
                    SessionSegment('过渡', session_label('A2', copy_mode), '4×50m 稳定节奏，休 20s'),
                    SessionSegment('主训练', session_label('EN1', copy_mode), '6×100m 稳定输出，休 20–30s；可根据能力改为 8×75m'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100–200m 放松游'),
                ],
                notes=['目标是提高周训练完成率，而不是单节课拼到很累。', '如果连续两次都很轻松，下周再增加一点主训练组数。']
            ),
            SessionPlan(
                title='第 2 次｜代谢刺激日',
                intention='给减脂用户一点更明确的代谢刺激，但仍保持可控。',
                total_distance=base_total,
                effort_explainer='以较高强度稳定训练为主，不需要全程冲刺。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '300m 轻松游 + 4×50m 逐渐提速'),
                    SessionSegment('主训练 1', session_label('EN1', copy_mode), '4×100m 稳定游，休 20–30s'),
                    SessionSegment('主训练 2', session_label('EN2', copy_mode), '6×50m 较高强度稳定训练，休 25–35s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '150m 放松游'),
                ],
                notes=['减脂用户依旧需要保留一部分较高强度，但占比不用太高。']
            ),
            SessionPlan(
                title='第 3 次｜恢复与技术日',
                intention='通过恢复和技术整理，提高下一次训练质量。',
                total_distance=f'{max(600, lower - 300)}–{max(900, upper - 300)} m',
                effort_explainer='轻松完成即可，避免把恢复课游成硬顶课。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '200–300m 轻松游'),
                    SessionSegment('技术', session_label('A2', copy_mode), '6×50m 技术动作练习，休 20s'),
                    SessionSegment('主训练', session_label('EN1', copy_mode), '4×100m 轻中强度，动作和呼吸放松'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100m 放松游'),
                ],
                notes=['状态差时，这节课可以直接作为本周主课保底完成。']
            ),
            SessionPlan(
                title='第 4 次｜可选补充课',
                intention='用于本周状态好时增加活动量，不追求复杂结构。',
                total_distance=f'{max(700, lower - 200)}–{max(1000, upper - 200)} m',
                effort_explainer='以轻松完成和额外消耗为主。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '200m 轻松游'),
                    SessionSegment('主训练', session_label('A2', copy_mode), '连续 400–800m 稳定游，必要时每 100m 停 10–15s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100m 放松游'),
                ],
                notes=['时间紧张时，可把这一节删掉，不影响本周主线。']
            )
        ]
    elif user_group == '备赛用户':
        bank = [
            SessionPlan(
                title='第 1 次｜EN2 主课',
                intention='建立比赛所需的节奏控制与阈值稳定性。',
                total_distance=base_total,
                effort_explainer='主训练以 EN2 为核心，根据项目类型调节距离。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '400m + 4×50m 技术/节奏'),
                    SessionSegment('预备', session_label('A2', copy_mode), '4×50m build，休 20s'),
                    SessionSegment('主训练', session_label('EN2', copy_mode), '8×100m 或 5×200m 阈值训练，休 20–30s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '200m 放松'),
                ],
                notes=['如果主项是短距离，可把主训练改为较短重复并提高质量。']
            ),
            SessionPlan(
                title='第 2 次｜速度与专项节奏',
                intention='保留比赛速度和专项动作质量。',
                total_distance=base_total,
                effort_explainer='短而快，但每组都要有质量，休息要给够。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '300–500m 轻松游'),
                    SessionSegment('激活', session_label('EN1', copy_mode), '4×50m 进入状态'),
                    SessionSegment('主训练 1', session_label('SP1', copy_mode), '8×25m 速度耐受，休 30–45s'),
                    SessionSegment('主训练 2', session_label('SP2', copy_mode), '6×50m 比赛节奏或 broken pace，休 45–60s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '150–200m 放松'),
                ],
                notes=['短距离主项可增加 SP 占比，中长距离主项以 EN2/EN3 为主。']
            ),
            SessionPlan(
                title='第 3 次｜恢复整合课',
                intention='在备赛期保留恢复窗口，避免持续堆疲劳。',
                total_distance=f'{max(800, lower - 400)}–{max(1200, upper - 400)} m',
                effort_explainer='恢复课依然要有质量，但不要冲强度。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '300m 轻松'),
                    SessionSegment('技术', session_label('A2', copy_mode), '6×50m 技术放松'),
                    SessionSegment('主训练', session_label('EN1', copy_mode), '4×100m 轻中强度，强调动作效率'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100–200m 放松'),
                ],
                notes=['恢复课完成度比总量更重要。']
            ),
            SessionPlan(
                title='第 4 次｜EN3 / 质量课',
                intention='做一节更接近比赛需求的高质量训练。',
                total_distance=base_total,
                effort_explainer='控制总量，确保高质量输出。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '400m + 4×50m build'),
                    SessionSegment('主训练', session_label('EN3', copy_mode), '6×75m 或 10×50m 高强有氧，休 30–45s'),
                    SessionSegment('补充', session_label('SP3', copy_mode), '4×15m 最大速度，完全恢复'),
                    SessionSegment('结束', session_label('A1', copy_mode), '200m 放松'),
                ],
                notes=['高质量课后 24–48 小时优先保证恢复。']
            )
        ]
    else:
        bank = [
            SessionPlan(
                title='第 1 次｜基础耐力日',
                intention='把本周训练节奏先稳定住。',
                total_distance=base_total,
                effort_explainer='以稳定可执行为第一优先。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '200–400m 轻松游 + 4×25m 技术练习'),
                    SessionSegment('过渡', session_label('A2', copy_mode), '4×50m 稳定节奏，休 20s'),
                    SessionSegment('主训练', session_label('EN1', copy_mode), '6×100m 或 4×150m 稳定输出，休 20–30s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100–200m 放松游'),
                ],
                notes=['如果你经常半途停掉训练，先保住完整度，不急着加复杂内容。']
            ),
            SessionPlan(
                title='第 2 次｜主刺激日',
                intention='本周最重要的一节课，用于推进能力。',
                total_distance=base_total,
                effort_explainer='根据目标安排 EN2 或 EN3 主训练。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '300–400m 轻松游 + 4×50m build'),
                    SessionSegment('预备', session_label('EN1', copy_mode), '4×50m 进入状态'),
                    SessionSegment('主训练', session_label('EN2', copy_mode) if goal != '提高速度' else session_label('EN3', copy_mode), '8×100m / 5×200m / 10×50m，依目标调整组长，休 20–40s'),
                    SessionSegment('结束', session_label('A1', copy_mode), '150–200m 放松'),
                ],
                notes=['这节课建议放在状态最好的一天。']
            ),
            SessionPlan(
                title='第 3 次｜恢复与技术日',
                intention='让节奏继续推进，而不是把疲劳越堆越高。',
                total_distance=f'{max(700, lower - 250)}–{max(1000, upper - 250)} m',
                effort_explainer='用轻中强度整理动作和呼吸。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '200–300m 轻松'),
                    SessionSegment('技术', session_label('A2', copy_mode), '6×50m 技术或腿部练习'),
                    SessionSegment('主训练', session_label('EN1', copy_mode), '4×100m 轻中强度 + 4×50m 放松节奏'),
                    SessionSegment('结束', session_label('A1', copy_mode), '100m 放松'),
                ],
                notes=['状态差时，这节课是保底完成课。']
            ),
            SessionPlan(
                title='第 4 次｜补充质量课',
                intention='给训练基础更好的用户一个额外推进窗口。',
                total_distance=base_total,
                effort_explainer='可选课，适合进阶训练者和比赛用户。',
                segments=[
                    SessionSegment('热身', session_label('A1', copy_mode), '300m 轻松'),
                    SessionSegment('主训练 1', session_label('EN2', copy_mode), '4×100m 稳定阈值'),
                    SessionSegment('主训练 2', session_label('SP1', copy_mode) if goal == '提高速度' else session_label('EN3', copy_mode), '6×25m 快速但动作完整，或 6×50m 高强有氧'),
                    SessionSegment('结束', session_label('A1', copy_mode), '150m 放松'),
                ],
                notes=['非进阶用户这一节可以直接不做。']
            )
        ]

    selected = bank[:max(1, min(sessions, len(bank)))]
    return selected


def cycle_focus_for_week(user_group: str, theme: str) -> str:
    if user_group == '减脂用户':
        mapping = {
            '建立节奏': '以完成率为主，形成每周稳定训练和轻微热量缺口。',
            '稳定推进': '逐步提高总量或主训练组数，不追求太高强度。',
            '重点刺激': '保留 1 节代谢刺激课，但整体仍以稳定执行为先。',
            '吸收与复盘': '控制疲劳，检查体重、围度和主观恢复。',
            '第二轮推进': '在前期适应的基础上，再次推进训练量和执行质量。',
            '测试与复盘': '观察体重、完成率、主观状态和坚持情况。',
            '吸收与微调': '适度减量，保证生活节奏与训练恢复同步。',
            '专项强化': '对减脂用户一般不做复杂专项，保持高完成率更重要。',
            '减量整合': '把节奏稳住，防止过度消耗导致反弹。'
        }
        return mapping.get(theme, '稳定推进训练执行和饮食节奏。')
    if user_group == '备赛用户':
        mapping = {
            '建立节奏': '建立专项节奏和训练分区秩序。',
            '稳定推进': '巩固 EN2 主训练与技术质量。',
            '重点刺激': '安排一周中的关键质量课，提高专项能力。',
            '吸收与复盘': '控制负荷，吸收上一阶段刺激。',
            '第二轮推进': '进入第二轮更明确的专项推进。',
            '测试与复盘': '进行小测试或比赛配速检验。',
            '吸收与微调': '减少无效疲劳，保留训练感。',
            '专项强化': '强化主项节奏、转身和速度质量。',
            '减量整合': '在减量中保留节奏锐度。'
        }
        return mapping.get(theme, '围绕专项节奏与质量推进。')
    mapping = {
        '建立节奏': '先形成固定训练节奏，把每节课做完整。',
        '稳定推进': '逐步提高主训练有效比例。',
        '重点刺激': '保留一节重点课推进能力。',
        '吸收与复盘': '避免连续堆疲劳，回看完成情况。',
        '第二轮推进': '在基础稳定后进行第二轮推进。',
        '测试与复盘': '检查配速、完成率和体感变化。',
        '吸收与微调': '稍微减量，吸收训练效果。',
        '专项强化': '根据目标加入更明确的专项刺激。',
        '减量整合': '整合节奏，降低疲劳。'
    }
    return mapping.get(theme, '持续推进训练质量。')


def estimate_swim_calories(weight_kg: Optional[float], duration_minutes: int, intensity_bucket: str) -> Dict:
    if not weight_kg:
        return {'estimated': None, 'range': None, 'method': '未提供体重，无法给出可靠热量估计。'}
    met = {'easy': 6.0, 'moderate': 8.0, 'hard': 10.0}.get(intensity_bucket, 7.5)
    base = 0.0175 * met * float(weight_kg) * duration_minutes
    low = int(base * 0.9)
    high = int(base * 1.1)
    return {'estimated': int(base), 'range': [low, high], 'method': '基于体重、时长与强度等级的区间估计。'}


def activity_multiplier(activity_level: str) -> float:
    return {
        '久坐': 1.2,
        '轻度活动': 1.35,
        '中度活动': 1.5,
        '较高活动': 1.7,
    }.get(activity_level, 1.35)


def estimate_bmr(profile: Dict) -> Optional[float]:
    weight = profile.get('weight_kg')
    height = profile.get('height_cm')
    age = profile.get('age')
    sex = profile.get('sex')
    if not all([weight, height, age, sex]):
        return None
    s = 5 if sex == '男' else -161
    return 10 * float(weight) + 6.25 * float(height) - 5 * int(age) + s


def nutrition_guidance(profile: Dict, distribution: Dict[str, int]):
    if profile['goal'] != '减脂' and profile['user_group'] != '减脂用户':
        return None, None
    weight = profile.get('weight_kg')
    duration = int(profile['session_duration'])
    bmr = estimate_bmr(profile)
    swim = estimate_swim_calories(weight, duration, 'moderate')
    maintenance = None
    target = None
    deficit = None
    macros = None
    if bmr:
        maintenance = int(bmr * activity_multiplier(profile.get('activity_level') or '轻度活动'))
        if swim.get('estimated'):
            maintenance += int(swim['estimated'] * 0.35)
        deficit = 350 if (weight or 0) < 75 else 450
        target = max(maintenance - deficit, int(bmr * 1.15))
    if weight and target:
        protein_g = round(float(weight) * 1.8)
        fat_g = round(float(weight) * 0.8)
        carb_kcal = max(target - protein_g * 4 - fat_g * 9, 0)
        carb_g = round(carb_kcal / 4)
        macros = {
            'protein_g': protein_g,
            'fat_g': fat_g,
            'carb_g': carb_g,
            'protein_pct': round(protein_g * 4 / target * 100),
            'fat_pct': round(fat_g * 9 / target * 100),
            'carb_pct': max(0, 100 - round(protein_g * 4 / target * 100) - round(fat_g * 9 / target * 100)),
        }
    calories = {
        'bmr': round(bmr) if bmr else None,
        'maintenance_kcal': maintenance,
        'training_day_target_kcal': target,
        'target_deficit_kcal': deficit,
        'single_session_burn': swim,
        'weekly_distribution': distribution,
        'note': '热量与消耗均为估计值，用于帮助形成可持续的减脂节奏，而不是医疗或营养处方。'
    }
    nutrition = {
        'summary': '优先保证蛋白与训练前后补碳，训练日不要靠极端少吃去拉赤字。',
        'macros': macros,
        'meals': [
            '训练前 60–120 分钟：少量主食 + 易消化蛋白，避免空腹完成完整训练。',
            '训练后 1 小时内：补充主食和蛋白，帮助恢复并减少暴食风险。',
            '非训练日：总热量可略低于训练日，但不要明显降低蛋白。',
        ]
    }
    return calories, nutrition


def build_cycle_overview(profile: Dict, week_plan: List[SessionPlan]) -> Optional[List[Dict]]:
    if profile['plan_scope'] != 'cycle':
        return None
    length = int(profile.get('cycle_length') or 4)
    overview = []
    load_cycle = ['低-中', '中', '中-高', '低']
    for idx, (week_name, theme) in enumerate(load_pattern_for_cycle(length), start=1):
        overview.append({
            'week_index': idx,
            'title': week_name,
            'theme': theme,
            'focus': cycle_focus_for_week(profile['user_group'], theme),
            'load_hint': load_cycle[(idx - 1) % 4],
            'session_count': profile['sessions_per_week'],
            'key_session': week_plan[min(len(week_plan) - 1, 1)].title,
        })
    return overview


def generate_plan(profile: Dict) -> Dict:
    distribution = zone_distribution(profile['goal'], profile['user_group'])
    weekly_sessions = build_session_templates(profile)
    guide = get_intensity_guide(profile.get('css_pace_seconds'))
    calories, nutrition = nutrition_guidance(profile, distribution)
    cycle_overview = build_cycle_overview(profile, weekly_sessions)

    warnings = []
    if profile.get('discomfort') and profile['discomfort'] != '没有明显不适':
        warnings.append('当前存在不适或恢复风险，系统已自动降低高强刺激比例。')
    if not profile.get('css_pace_seconds'):
        warnings.append('当前未使用 CSS 配速，EN 区间以训练目标与体感控制为主。')
    if profile['user_group'] == '爱好者':
        warnings.append('爱好者默认展示通俗强度描述，专业区间可在“专业说明”中展开查看。')

    return {
        'summary': summarize_profile(profile),
        'plan_scope': profile['plan_scope'],
        'headline': '默认给出本周可直接执行的计划；只有在你主动选择时，才展开完整周期。',
        'weekly_plan': [s.to_dict() for s in weekly_sessions],
        'cycle_overview': cycle_overview,
        'intensity_guide': guide,
        'zone_distribution': distribution,
        'coach_notes': [
            '优先保证完成率，再追求更高强度。',
            '每次训练至少保留热身和放松，不建议只做主训练。',
            '当睡眠不足、疲劳偏高或出现不适时，优先回退到 A1/A2/EN1。',
        ],
        'warnings': warnings,
        'nutrition': nutrition,
        'calories': calories,
        'data_precision': 'CSS 增强版' if profile.get('css_pace_seconds') else '经验规则版',
        'presentation_mode': user_copy_mode(profile['user_group'])
    }


# ---------- Feedback ----------

def analyze_watch_metrics(plan: Dict, session_index: Optional[int], metrics: Dict) -> Dict:
    weekly = plan.get('weekly_plan') if isinstance(plan, dict) else None
    session = None
    if weekly and session_index is not None and 0 <= session_index < len(weekly):
        session = weekly[session_index]
    planned_range = None
    if session and session.get('total_distance'):
        numbers = re.findall(r'(\d+)', session['total_distance'])
        if len(numbers) >= 2:
            planned_range = (int(numbers[0]), int(numbers[1]))
    actual_distance = metrics.get('actual_distance_m')
    completion = None
    ratio = None
    if planned_range and actual_distance:
        _, upper = planned_range
        ratio = round(actual_distance / upper, 2)
        if ratio >= 0.9:
            completion = '基本完成'
        elif ratio >= 0.65:
            completion = '完成了一大部分'
        else:
            completion = '完成不足'
    return {
        'planned_distance_range': planned_range,
        'actual_distance_m': actual_distance,
        'completion_by_distance': completion,
        'completion_ratio': ratio,
        'ocr_text': metrics.get('ocr_text')
    }


def analyze_feedback(profile: Dict, plan_data: Dict, payload: Dict) -> Dict:
    fatigue = int(payload['fatigue_score'])
    discomfort = payload['discomfort_feedback']
    sleep_status = payload['sleep_status']
    completion = payload['completion_status']
    metrics = payload.get('screenshot_metrics') or {}
    session_index = payload.get('session_index')
    watch = analyze_watch_metrics(plan_data, session_index, metrics)

    high_risk = discomfort != '没有明显不适' or fatigue >= 9
    conservative = fatigue >= 7 or sleep_status in ['5 小时以下', '5–6 小时'] or completion in ['只完成了一小部分', '没有完成']
    progress = fatigue <= 4 and discomfort == '没有明显不适' and sleep_status in ['6–7 小时', '7 小时以上'] and completion == '完成了全部训练'
    if watch.get('completion_by_distance') == '完成不足':
        conservative = True

    if high_risk:
        judgment = '本次训练存在明显风险信号。'
        direction = '下次先回退到恢复课和基础有氧，不建议继续推进。'
        recommended_zone = 'A1 / A2'
        next_week_action = '回调'
        next_session = {
            'goal': '优先恢复节奏，先保证训练安全。',
            'warmup': '轻松游 200m + 简单肩髋活动。',
            'main': '6×50m 轻松游，充分休息；必要时减少组数。',
            'cooldown': '100m 放松游。',
            'note': '如果不适持续或加重，应暂停高刺激训练并线下评估。'
        }
    elif conservative:
        judgment = '本次训练整体偏累或完成度不足。'
        direction = '下次建议保守一点，先把节奏和完成率拉回来。'
        recommended_zone = 'A2 / EN1'
        next_week_action = '维持或小幅回调'
        next_session = {
            'goal': '恢复节奏，把完整训练做下来。',
            'warmup': '200–300m 轻松游 + 4×50m 放松节奏。',
            'main': '4×100m EN1，组间休 25–35s；再做 4×50m A2。',
            'cooldown': '100–150m 放松。',
            'note': '如果本次是生活节奏导致的偏累，下周再决定是否恢复主刺激。'
        }
    elif progress:
        judgment = '本次训练完成度和主观恢复都比较理想。'
        direction = '下次可以在保持结构的前提下小幅推进。'
        recommended_zone = 'EN2 / EN3'
        next_week_action = '推进'
        next_session = {
            'goal': '保持当前结构，在主训练中轻微加码。',
            'warmup': '300m 轻松游 + 4×50m build。',
            'main': '5×100m EN2，组间休 20–30s；再做 4×50m EN2/EN3。',
            'cooldown': '150m 放松游。',
            'note': '推进幅度不宜太大，优先保证动作质量和节奏完整。'
        }
    else:
        judgment = '本次训练整体可接受。'
        direction = '下次维持当前结构，继续观察恢复和完成率。'
        recommended_zone = 'EN1 / EN2'
        next_week_action = '维持'
        next_session = {
            'goal': '继续把训练完整做下来。',
            'warmup': '200–300m 轻松游 + 4×50m 进入状态。',
            'main': '4×100m EN1/EN2，组间休 25–30s；补 4×50m 稳定输出。',
            'cooldown': '100–150m 放松。',
            'note': '优先保证执行稳定，不急于增加更多训练量。'
        }

    adherence_label = watch.get('completion_by_distance') or '未提供客观训练截图数据'
    return {
        'judgment': judgment,
        'direction': direction,
        'recommended_zone': recommended_zone,
        'next_week_action': next_week_action,
        'explanation': '系统同时参考了主观疲劳、睡眠、不适以及训练完成情况，判断当前更适合推进、维持还是回调。',
        'watch_analysis': watch,
        'adherence_label': adherence_label,
        'next_session': next_session,
    }


# ---------- Growth / Rollover ----------

def build_rollover_profile(profile: Dict, progress: Dict) -> Dict:
    """Return a slightly adjusted profile for next-week rolling plan generation."""
    updated = dict(profile)
    overview = progress.get('overview', {}) if progress else {}
    completion = float(overview.get('avg_completion_rate') or 0)
    fatigue = float(overview.get('avg_fatigue') or 0)
    status = overview.get('current_status') or '维持推进'
    sessions = int(updated.get('sessions_per_week') or 3)
    duration = int(updated.get('session_duration') or 45)

    notes = []
    if status == '需要回调' or fatigue >= 7:
        updated['sessions_per_week'] = max(2, sessions - 1) if sessions >= 3 else sessions
        updated['session_duration'] = max(30, duration - 5)
        notes.append('滚动更新：最近完成率或恢复偏弱，下一周先降低压力，保住训练连续性。')
        if updated.get('discomfort') == '没有明显不适':
            updated['discomfort'] = '近期恢复压力偏高，下一周先回调负荷'
    elif completion >= 88 and fatigue <= 5:
        updated['sessions_per_week'] = min(6, sessions + 1) if sessions <= 3 and updated.get('user_group') in {'进阶训练者', '备赛用户'} else sessions
        updated['session_duration'] = min(90, duration + (5 if duration <= 60 else 0))
        notes.append('滚动更新：近期完成率和恢复质量较好，下一周可小幅推进主刺激。')
    else:
        notes.append('滚动更新：延续当前节奏，以稳定完成率和可恢复性为首要目标。')

    if updated.get('plan_scope') != 'cycle':
        updated['cycle_length'] = 4
    updated['extra_note'] = ((updated.get('extra_note') or '').strip() + '\n' + '\n'.join(notes)).strip()
    return updated


def growth_stage_from_progress(progress: Dict) -> Dict:
    overview = progress.get('overview', {}) if progress else {}
    feedback_count = int(overview.get('feedback_count') or 0)
    completion = float(overview.get('avg_completion_rate') or 0)
    fatigue = float(overview.get('avg_fatigue') or 0)

    if feedback_count < 2:
        return {'code': 'foundation', 'title': '建立节奏期', 'description': '先建立每周稳定执行和反馈习惯。'}
    if completion >= 85 and fatigue <= 5.5:
        return {'code': 'progressing', 'title': '稳步推进期', 'description': '完成率与恢复都较好，可以进入渐进提升。'}
    if fatigue >= 7 or overview.get('current_status') == '需要回调':
        return {'code': 'recovery', 'title': '恢复整合期', 'description': '当前更需要守住恢复和连续性，而不是继续加码。'}
    return {'code': 'stable', 'title': '稳定巩固期', 'description': '训练执行在可接受范围内，重点是稳住节奏与动作质量。'}
