"""Render a 60-second original motion-graphics film with synthetic UI data.

Media-only dependencies: pillow, numpy, imageio-ffmpeg. macOS say supplies
the Tingting synthetic voice. Pass --font for a Chinese font on other setups.
The training application does not require any of these packages.
"""
import argparse
import math
from datetime import date
import sys
import subprocess
import tempfile
import wave
from pathlib import Path
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ai4boji.core import Service, seed_demo
from ai4boji.storage import Store
W, H, FPS = 1920, 1080, 30
BLUE, PURPLE, ROSE = '#6F8EAE', '#7F7788', '#A65F68'
INK, MUTED, BG = '#373D43', '#747A80', '#FAFBFC'
SCENES = [
    ('从哪里开始？', '想练出薄肌，却不知道每天该做什么？', 'Want to build a leaner, stronger body, but unsure where to begin?'),
    ('AI4薄肌', '认识 AI for 薄肌，你的 Codex 个人训练伙伴。', 'Meet AI4薄肌, your personal training companion powered by Codex.'),
    ('先理解你', '从你的时间、器械和训练日出发，建立专属档案。', 'Start with your time, equipment and training days. Build your own profile.'),
    ('今天，感觉怎么样？', '睡得好吗？精力如何？用真实状态，更新今天的安排。', 'How did you sleep? How is your energy? Let today’s state guide the plan.'),
    ('让每一步，都清楚', '动作、组次、休息，还有为什么这样安排，都清晰可见。', 'Exercises, sets, rest and the reasons behind your plan, all in one place.'),
    ('记录真实完成', '练了多少，就记录多少。也可以更正，让进步有据可依。', 'Record what you actually did. Correct it when needed. Keep progress grounded.'),
    ('记住对你重要的事', '保存你的偏好和长期记忆，下次对话，不必从头开始。', 'Keep your preferences and long-term memory. Pick up where you left off.'),
    ('看见一点一滴', '用日历、曲线和回顾，看见每一次投入，慢慢积累。', 'See your efforts add up through calendars, charts and reflections.'),
    ('和 Codex，一起行动', '打开项目，告诉 Codex，你今天的状态。让下一步更具体。', 'Open the project. Tell Codex how you feel today. Make the next step concrete.'),
    ('每天，靠近更好的自己', 'AI for 薄肌，现已开源。从今天开始，找到自己的节奏。', 'AI4薄肌 is open source. Start today, and find your own pace.'),
]


def run(*args):
    subprocess.run([str(a) for a in args], check=True, stdout=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--font')
    parser.add_argument('--output', default=str(ROOT / 'media'))
    parser.add_argument('--work', default=None)
    parser.add_argument('--reuse-audio', action='store_true', help='Reuse cached voice-*.aiff clips in --work')
    args = parser.parse_args()
    font_path = args.font
    if not font_path:
        found = list(Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font8').glob('*/AssetData/PingFang.ttc'))
        if not found:
            raise SystemExit('Pass --font with a Chinese TrueType/OpenType font.')
        font_path = str(found[0])
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    scratch = Path(args.work or tempfile.mkdtemp(prefix='ai4boji-film-')); scratch.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    @lru_cache(None)
    def font(size):
        return ImageFont.truetype(font_path, size)

    dark = [False]

    def text(draw, xy, string, size=36, fill=INK, anchor=None):
        if dark[0]:
            fill = {INK:'#F5F7FA', MUTED:'#B1BFCD', BLUE:'#A4BED8', PURPLE:'#BCB0CB', ROSE:'#E2A0AB'}.get(fill, fill)
        draw.text(xy, string, font=font(size), fill=fill, anchor=anchor)

    def roundbox(draw, box, fill='white', outline='#E4E7EA', radius=24):
        if dark[0] and fill in ['white','#F1F4F7']:
            fill,outline = '#233A50','#3F566D'
        draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)

    # Each sentence is independently fitted into its six-second scene.
    sr = 48000
    voice = np.zeros(60 * sr, dtype=np.float32)
    timing = []
    for i, (_, line, _) in enumerate(SCENES):
        src, wav = scratch / f'voice-{i}.aiff', scratch / f'voice-{i}.wav'
        if not (args.reuse_audio and src.exists()):
            run('say', '-v', 'Tingting', '-r', '190', '-o', src, line)
        run(ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-ar', sr, '-ac', '1', wav)
        with wave.open(str(wav)) as f:
            samples = np.frombuffer(f.readframes(f.getnframes()), '<i2').astype(np.float32) / 32768
        duration = len(samples) / sr
        if duration > 5.35:
            fitted = scratch / f'fitted-{i}.wav'
            run(ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', wav, '-af', f'atempo={duration / 5.35:.5f}', fitted)
            with wave.open(str(fitted)) as f:
                samples = np.frombuffer(f.readframes(f.getnframes()), '<i2').astype(np.float32) / 32768
        samples = samples / max(.1, float(np.max(np.abs(samples)))) * .68
        start = int((i * 6 + .35) * sr)
        voice[start:start+len(samples)] = samples
        timing.append({'scene':i+1, 'seconds':round(len(samples)/sr, 3)})

    # Original electronic bed: soft pads, syncopated plucks and a restrained pulse.
    t = np.arange(60 * sr) / sr
    music = np.zeros_like(t)
    chords = [(130.81,164.81,196,246.94),(110,130.81,164.81,196),(87.31,130.81,164.81,220),(98,146.83,196,246.94)]
    for i in range(10):
        start, end = int(i*6*sr), int((i+1)*6*sr)
        u = np.arange(end-start)/sr
        env = np.minimum(u/1.1,1)*np.minimum((6-u)/1.1,1)
        chord = chords[i % 4]
        for f in chord:
            music[start:end] += .006 * env * np.sin(2*np.pi*f*u + .1*np.sin(2*np.pi*.3*u))
        for beat in range(8):
            local = u-beat*.75
            pluck = np.where(local>=0, np.exp(-np.maximum(local,0)*7),0)
            music[start:end] += .01*pluck*np.sin(2*np.pi*chord[beat%4]*4*local)
            if beat % 2 == 0:
                positive=np.maximum(local,0)
                kick=np.where(local>=0,np.exp(-positive*14),0)
                music[start:end] += .028*kick*np.sin(2*np.pi*(48*positive+4*(1-np.exp(-positive*22))))
    duck = 1-.65*(np.abs(voice)>.008)
    audio = voice + music*duck
    audio *= np.minimum(t/.4,1)*np.minimum((60-t)/.9,1)
    audio_path = scratch/'soundtrack.wav'
    with wave.open(str(audio_path),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes(np.repeat((np.clip(audio,-1,1)*32767).astype('<i2')[:,None],2,axis=1).tobytes())

    # Render real rule-engine output as large native text, never shrink a dashboard screenshot.
    class FilmService(Service):
        def today(self):
            return '2026-10-16'

    with tempfile.TemporaryDirectory() as tmp:
        service = FilmService(Store(tmp))
        seed_demo(service)
        service.save_checkin({'date':service.today(), 'sleep_hours':7.5, 'energy':4, 'soreness':1, 'pain':False, 'minutes':20})
        service.generate_plan()
        film_state = service.state()
    film_plan, film_report = film_state['plan']['payload'], film_state['report']

    def ease(value):
        return 1 - (1-max(0,min(value,1)))**3

    def scene_frame(i, local):
        dark[0] = i in (0,1,8,9)
        im=Image.new('RGB',(W,H),'#172A3D' if dark[0] else BG);d=ImageDraw.Draw(im)
        # Moving orbital field and fine grid give each scene a continuous sense of motion.
        grid_color = '#20384E' if dark[0] else '#F0F2F5'
        for x in range(-100,2000,100):
            shift=int((local*12+i*25)%100)
            d.line((x+shift,120,x+shift,H-140),fill=grid_color,width=1)
        for j,col in enumerate(['#2B445E','#3A3D59','#563E51'] if dark[0] else ['#E5EDF4','#EBE7EE','#F0E5E8']):
            radius=270+j*90
            cx=1640+int(math.sin(local*.5+j)*65);cy=400+int(math.cos(local*.4+j)*55)
            d.arc((cx-radius,cy-radius,cx+radius,cy+radius),start=local*17+j*80,end=local*17+j*80+230,fill=col,width=2)
        enter = 1-(1-min(local/1.1,1))**3
        dy=int((1-enter)*40)
        # Persistent brand, three-color signature, and scene progress.
        for j,col in enumerate([BLUE,PURPLE,ROSE]): d.ellipse((96+j*25,64,109+j*25,77),fill=col)
        text(d,(194,48),'AI4薄肌',29)
        text(d,(1820,62),f'{i+1:02d} / 10',23,MUTED,'ra')
        d.line((96,966,1824,966),fill='#3F566D' if dark[0] else '#E1E4E8',width=2)
        d.line((96,966,96+int(1728*(i*6+local)/60),966),fill=[BLUE,PURPLE,ROSE][i%3],width=5)
        text(d,(960,1000),SCENES[i][1].replace('AI for 薄肌','AI4薄肌'),36,INK,'ma')
        text(d,(1820,927),'合成示例数据 · v0.1',19,MUTED,'ra')
        if i in (0,1,9):
            cx,cy=1425,500
            for j,col in enumerate([BLUE,PURPLE,ROSE]):
                phase=local*.42+j*2.094
                x=cx+math.cos(phase)*64;y=cy+math.sin(phase)*64
                d.ellipse((x-230,y-230,x+230,y+230),outline=col,width=3)
                dotx=x+230*math.cos(local*.9+j*2);doty=y+230*math.sin(local*.9+j*2)
                d.ellipse((dotx-9,doty-9,dotx+9,doty+9),fill=col)
            text(d,(1425,475),'薄',135,PURPLE,'mm')
            if i==0:
                text(d,(100,240+dy),'想练出薄肌，',76)
                text(d,(100,350+int((1-ease((local-.2)/.9))*45)),'却不知道怎么开始？',76)
                text(d,(105,520),'从每天的一点行动开始。',34,MUTED)
                for j,label in enumerate(['我的时间','我的状态','我的节奏']):
                    roundbox(d,(105+j*245,660,320+j*245,735))
                    text(d,(212+j*245,680),label,27,[BLUE,PURPLE,ROSE][j],'ma')
            elif i==1:
                text(d,(100,215+dy),'AI4薄肌',140)
                text(d,(108,400),'Codex 驱动的个人训练伙伴',45,BLUE)
                for j,label in enumerate(['每日指导','长期记忆','进步可视化']):
                    px=110+j*270;py=535+int((1-ease((local-.7-j*.25)/.6))*40)
                    roundbox(d,(px,py,px+245,py+80));text(d,(px+122,py+18),label,32,[BLUE,PURPLE,ROSE][j],'ma')
                text(d,(110,690),'中文优先 · 中英双语 · 本地优先',28,PURPLE)
            else:
                text(d,(100,205+dy),'AI4薄肌',112)
                text(d,(108,385),'每天，靠近更好的自己。',52)
                roundbox(d,(105,530,715,620),ROSE,ROSE)
                text(d,(410,550),'现已开源 · 即刻开始 ↗',33,'white','ma')
                text(d,(110,690),'selen-suyue.github.io/ai4boji',33,BLUE)
                text(d,(110,753),'github.com/Selen-Suyue/ai4boji',28,MUTED)
        else:
            kicker=['','','01 / 理解你的起点','02 / 跟随今天的状态','03 / 看得懂的计划','04 / 记录实际行动','05 / 记忆延续','06 / 进步可见','07 / 搭配 CODEX'][i]
            text(d,(100,175+dy),kicker,25,[BLUE,PURPLE,ROSE][i%3])
            title=SCENES[i][0]
            if i == 4:
                text(d,(100,245+dy),'小林，今天练这三项。',66)
                text(d,(1795,250),f'{film_plan["minutes"]} 分钟以内',46,ROSE,'ra')
                for j,exercise in enumerate(film_plan['exercises']):
                    row_enter=ease((local-.35-j*.22)/.8)
                    x=105+int((1-row_enter)*170);y=380+j*145
                    roundbox(d,(x,y,x+1710,y+125))
                    d.rounded_rectangle((x,y,x+7,y+125),3,fill=[BLUE,PURPLE,ROSE][j%3])
                    text(d,(x+38,y+29),f'0{j+1}',40,[BLUE,PURPLE,ROSE][j%3])
                    text(d,(x+145,y+24),exercise['name']['zh-CN'],48)
                    text(d,(x+830,y+39),f'组间休息 {exercise["rest_seconds"]} 秒',34,MUTED)
                    text(d,(x+1630,y+23),f'{exercise["sets"]} × {exercise["reps"]}',54,PURPLE,'ra')
                text(d,(110,855),'按你的时间、器械与今日状态生成 · 先热身，动作保持可控',32,MUTED)
            elif i == 7:
                text(d,(100,245+dy),'进步，有自己的节奏。',66)
                roundbox(d,(105,380,1190,865));roundbox(d,(1230,380,1815,865))
                text(d,(150,410),'体重记录',40,BLUE);text(d,(1135,420),'kg',30,MUTED,'ra')
                points=film_report['weights'];values=[p['value'] for p in points]
                lo,hi=min(values)-.2,max(values)+.2
                dates=[date.fromisoformat(p['date']).toordinal() for p in points]
                xs=[250+(day-dates[0])/max(1,dates[-1]-dates[0])*860 for day in dates]
                ys=[725-(v-lo)/(hi-lo)*210 for v in values]
                for tick in range(3):
                    value=lo+(hi-lo)*tick/2;y=725-tick*105
                    d.line((245,y,1120,y),fill='#E5E8EB',width=2)
                    text(d,(213,y-20),f'{value:.1f}',32,MUTED,'ra')
                fraction=ease((local-.6)/3.4)*(len(points)-1)
                for j in range(len(points)-1):
                    f=min(max(fraction-j,0),1)
                    if f>0:d.line((xs[j],ys[j],xs[j]+(xs[j+1]-xs[j])*f,ys[j]+(ys[j+1]-ys[j])*f),fill=ROSE,width=6)
                for j in range(len(points)):
                    if j<=fraction:d.ellipse((xs[j]-7,ys[j]-7,xs[j]+7,ys[j]+7),fill=ROSE)
                for j in [0,len(points)//2,len(points)-1]:text(d,(xs[j],765),points[j]['date'][5:].replace('-','/'),30,MUTED,'ma')
                text(d,(1280,420),'近 14 天 · 真实记录',32,MUTED)
                metric=ease((local-.3)/1.8)
                text(d,(1290,510),str(round(film_report['training_days']*metric)),100,BLUE);text(d,(1435,566),'天训练',36)
                text(d,(1288,675),str(round(film_report['total_minutes']*metric)),100,ROSE);text(d,(1540,731),'分钟',36)
                text(d,(110,890),'连线仅连接已记录的测量点 · 不预测未来',28,MUTED)
            else:
                text(d,(100,255+dy),title,70)
                if i==2:
                    cards=[('20 分钟','每天的可用时间',BLUE),('徒手 / 哑铃','身边的训练器械',PURPLE),('每周 1–3 天','适合起步的频率',ROSE)]
                    for j,(v,label,col) in enumerate(cards):
                        x=105+j*580;y=440+int((1-min(max(local-j*.18,0)/.8,1))*30)
                        roundbox(d,(x,y,x+540,y+330));text(d,(x+40,y+55),f'0{j+1}',26,col);text(d,(x+40,y+135),v,56,col);text(d,(x+40,y+245),label,28,MUTED)
                elif i==3:
                    vals=[('睡眠','7.5 小时',BLUE),('精力','4 / 5',PURPLE),('今天可用','20 分钟',ROSE)]
                    for j,(label,v,col) in enumerate(vals):
                        x=105+j*580;roundbox(d,(x,425,x+540,690));text(d,(x+35,460),label,29,MUTED);text(d,(x+35,535),v,66,col)
                    text(d,(110,765),'安排随状态调整 · 疲惫时恢复 · 疼痛时暂停自动力量计划',29,MUTED)
                elif i==5:
                    roundbox(d,(105,425,1100,835));text(d,(145,465),'今日训练记录',30,BLUE)
                    text(d,(145,555),str(round(18*ease((local-.35)/1.5))),110,ROSE);text(d,(310,620),'分钟',34,MUTED)
                    text(d,(145,735),'坐椅深蹲  2 × 8    /    难度 5 / 10',31)
                    text(d,(1200,500),'真实完成',58,PURPLE);text(d,(1200,600),'支持更正',42,MUTED);text(d,(1200,690),'保留版本',42,MUTED)
                elif i==6:
                    labels=[('偏好','周末更喜欢上午训练',BLUE),('事实','保留你确认的信息',PURPLE),('AI 推断','单独标记，等待确认',ROSE)]
                    for j,(kind,line,col) in enumerate(labels):
                        y=420+j*140;offset=int((1-ease((local-.3-j*.3)/.7))*160)
                        roundbox(d,(105+offset,y,1385+offset,y+112));text(d,(145+offset,y+29),kind,32,col);text(d,(385+offset,y+29),line,32)
                    text(d,(1480,515),'下一次',42,MUTED);text(d,(1480,590),'接着来。',51,PURPLE)
                elif i==8:
                    roundbox(d,(105,420,1815,830),'#F1F4F7')
                    text(d,(150,455),'YOU → CODEX',25,BLUE)
                    text(d,(150,525),'使用 $ai4boji，我今天只有 20 分钟。',46)
                    count=int(min(max((local-1.8)/1.4,0),1)*3)
                    for j,label in enumerate(['读取档案与近期记录','更新今天的状态','保存后读回验证']):
                        x=150+j*540;roundbox(d,(x,665,x+485,760),'white');text(d,(x+25,694),('✓ ' if j<count else '· ')+label,29,[BLUE,PURPLE,ROSE][j])
        return im

    poster=scene_frame(1,3)
    poster.save(out/'promo-poster.jpg',quality=94)
    contact=Image.new('RGB',(960,540*2),'white')
    for j,i in enumerate([0,2,4,6,7,9]):
        contact.paste(scene_frame(i,3).resize((480,270)),((j%2)*480,(j//2)*270))
    contact.crop((0,0,960,810)).save(scratch/'contact-sheet.jpg',quality=90)
    for scene,name in [(4,'plan-detail'),(7,'progress-detail')]:scene_frame(scene,4.5).save(scratch/(name+'.png'))
    target=out/'AI4薄肌-60s-v2.mp4'
    cmd=[ffmpeg,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(audio_path),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-t','60',str(target)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    previous=None
    for n in range(60*FPS):
        seconds=n/FPS;i=int(seconds//6);local=seconds-i*6
        current=scene_frame(i,local)
        if i>0 and local<.35:
            if previous is None:previous=scene_frame(i-1,5.99)
            # A brief brand-color wipe reveals the next scene without shrinking its text.
            boundary=int(W*ease(local/.35))
            transition=previous.copy();transition.paste(current.crop((0,0,boundary,H)),(0,0))
            ImageDraw.Draw(transition).rectangle((boundary,0,min(boundary+18,W),H),fill=[BLUE,PURPLE,ROSE][i%3])
            current=transition
        else:previous=None
        proc.stdin.write(current.tobytes())
        if n%(6*FPS)==0:print(f'Rendered scene {i+1}/10',flush=True)
    proc.stdin.close()
    if proc.wait():raise SystemExit('Video encoder failed')
    def stamp(value,sep='.'):
        return f'00:{int(value)//60:02d}:{int(value)%60:02d}{sep}000'
    for language in ['zh','en']:
        entries=[]
        for i,(_,zh,en) in enumerate(SCENES):
            caption=(zh.replace('AI for 薄肌','AI4薄肌') if language=='zh' else en)
            entries.append(f'{stamp(i*6)} --> {stamp((i+1)*6)}\n{caption}\n')
        (out/f'promo-{language}.vtt').write_text('WEBVTT\n\n'+'\n'.join(entries),encoding='utf-8')
    (out/'promo-zh.srt').write_text('\n'.join(f'{i+1}\n{stamp(i*6,",")} --> {stamp((i+1)*6,",")}\n{zh.replace("AI for 薄肌","AI4薄肌")}\n' for i,(_,zh,_) in enumerate(SCENES)),encoding='utf-8')
    print('Audio scene durations:',timing,flush=True)
    print('Saved',target,target.stat().st_size,flush=True)


if __name__ == '__main__':
    main()
