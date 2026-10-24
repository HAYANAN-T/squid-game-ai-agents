"""Capture five genuine Chromium screenshots of the running Canvas replay.
Reads the generated HTML into the browser; no external network or HTTP server required.
"""
from pathlib import Path
import argparse, shutil
from playwright.sync_api import sync_playwright

p=argparse.ArgumentParser()
p.add_argument('--world',default='world/squid_game_2d_world.html')
p.add_argument('--output',default='../article_assets')
a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
slugs=['red_light','dalgona','tug_of_war','marbles','glass_bridge']

with sync_playwright() as pw:
    system=shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('chrome')
    opts={'headless':True}
    if system:opts['executable_path']=system
    browser=pw.chromium.launch(**opts)
    page=browser.new_page(viewport={'width':1500,'height':1030},device_scale_factor=1.3)
    errors=[]
    page.on('pageerror',lambda exc:errors.append(str(exc)))
    page.set_content(Path(a.world).read_text(encoding='utf8'),wait_until='load')
    page.wait_for_timeout(100)
    for i,slug in enumerate(slugs):
        page.evaluate(f'chooseRound({i})')
        page.wait_for_timeout(100)
        path=out/f'actual_2d_world_round_{i+1}_{slug}.png'
        page.screenshot(path=str(path),full_page=True)
        print(f'Round {i+1}: {path} ({path.stat().st_size} bytes)')
    browser.close()
    if errors:raise RuntimeError('Browser JavaScript errors: '+str(errors))
