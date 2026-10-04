// 실제 SQL을 재실행하고 결과 문서를 Edge/Playwright로 캡처한다.
// 사용: node scripts/capture-results.cjs <Python 실행 파일>
// 이미지 재생성에만 Playwright와 Microsoft Edge가 필요하다.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const run = spawnSync(process.argv[2] || 'python', [path.join(root, 'run.py')], {
  cwd: root, stdio: 'inherit', windowsHide: true,
});
if (run.error) throw run.error;
if (run.status !== 0) process.exit(run.status || 1);

const temporary = path.join(root, 'output', 'playwright', 'sql-captures');
const destination = path.join(root, 'results', 'screenshots');
fs.mkdirSync(temporary, { recursive: true });
fs.mkdirSync(destination, { recursive: true });
const escape = value => value.replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character]);
const environment = fs.readFileSync(path.join(root, 'results', '00_environment.txt'), 'utf8');
const versions = environment.split(/\r?\n/).slice(0, 2).join(' · ');
const files = fs.readdirSync(path.join(root, 'results'))
  .filter(name => /^[qbme]\d{2}\.txt$/.test(name)).sort();
if (files.length !== 29) throw new Error(`Expected 29 execution records, got ${files.length}`);

function resultMarkup(value) {
  const lines = value.trim().split('\n');
  if (lines[0].includes('\t')) {
    const summary = lines.pop();
    const headers = lines.shift().split('\t');
    return '<table><thead><tr>' + headers.map(item => `<th>${escape(item)}</th>`).join('')
      + '</tr></thead><tbody>' + lines.map(line => '<tr>'
        + line.split('\t').map(item => `<td>${escape(item)}</td>`).join('') + '</tr>').join('')
      + `</tbody></table><p class="summary">${escape(summary)}</p>`;
  }
  return `<pre class="result">${escape(value.trim())}</pre>`;
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const captures = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
    for (const filename of files) {
      const text = fs.readFileSync(path.join(root, 'results', filename), 'utf8').replace(/\r\n/g, '\n');
      const sha256 = crypto.createHash('sha256').update(text).digest('hex');
      const title = text.split('\n')[0];
      const blocks = text.split('\nSQL:\n').slice(1).map((block, index) => {
        const separator = block.indexOf('\nRESULT:\n');
        if (separator < 0) throw new Error(`Missing result: ${filename}`);
        return `<section><h2>실행 ${index + 1} · SQL</h2><pre>${escape(block.slice(0, separator))}</pre>`
          + '<h2>실제 실행 결과</h2>' + resultMarkup(block.slice(separator + '\nRESULT:\n'.length)) + '</section>';
      });
      if (!blocks.length) throw new Error(`Missing SQL: ${filename}`);
      const html = `<!doctype html><html lang="ko"><meta charset="utf-8"><title>${escape(title)}</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#eef2f6;color:#182838;font-family:"Malgun Gothic",sans-serif;font-size:16px}
main{width:1360px;margin:28px auto;background:white;padding:34px 40px;border:1px solid #ccd7df;border-radius:12px}
.label{color:#176d66;font-weight:700;font-size:15px}h1{font-size:25px;line-height:1.5;margin:12px 0 16px}
.meta,footer{color:#536576;font-size:14px;line-height:1.7}section{border-top:1px solid #dce4eb;margin-top:26px;padding-top:14px}
h2{font-size:16px;margin:15px 0 10px}pre{font-family:Consolas,"Malgun Gothic",monospace;font-size:16px;line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f9;padding:16px;border-radius:6px;margin:0}
pre.result{background:#eaf5f2}table{width:100%;border-collapse:collapse;table-layout:auto;font-size:16px}
th,td{padding:10px 13px;text-align:left;border:1px solid #d6e0e7;overflow-wrap:anywhere}th{background:#eaf2f5}
tr:nth-child(even){background:#f8fafb}.summary{font-family:Consolas,monospace;color:#536576}footer{border-top:1px solid #dce4eb;margin-top:28px;padding-top:18px}
</style><main><div class="label">CODYSSEY B6-1 · SQLite 실행 결과 캡처</div>
<h1>${escape(title)}</h1><div class="meta">${escape(versions)}<br>원본: results/${filename}<br>SHA-256 (LF 정규화): ${sha256}</div>
${blocks.join('')}<footer>실제 SQL 재실행으로 저장한 결과 문서를 브라우저에 표시해 캡처했습니다.<br>
SQLite 실행 로그를 읽기 쉬운 문서로 표시한 화면이며, 결과값은 원본 텍스트와 동일합니다.</footer></main></html>`;
      fs.writeFileSync(path.join(temporary, filename.replace('.txt', '.html')), html, 'utf8');
      await page.setContent(html, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const dimensions = await page.evaluate(() => ({
        width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight,
        overflow: document.documentElement.scrollWidth > window.innerWidth,
      }));
      if (dimensions.overflow) throw new Error(`Horizontal overflow: ${filename}`);
      const imageName = filename.replace('.txt', '.png');
      await page.screenshot({ path: path.join(temporary, imageName), fullPage: true });
      fs.copyFileSync(path.join(temporary, imageName), path.join(destination, imageName));
      captures.push({ source: `results/${filename}`, source_sha256_lf: sha256,
        screenshot: `results/screenshots/${imageName}`, width: dimensions.width, height: dimensions.height });
    }
    fs.writeFileSync(path.join(destination, 'manifest.json'), JSON.stringify({
      engine: versions, browser: `Microsoft Edge ${browser.version()}`,
      method: 'Actual SQLite execution -> unchanged result text -> browser document -> Playwright screenshot',
      captures,
    }, null, 2) + '\n');
    const index = ['# SQL 실행 결과 스크린샷', '',
      '핵심 Q01~Q16 및 보너스·보완 B01~B04, M01~M03, E01~E06의 실제 결과 문서를 캡처했다.',
      '생성 과정과 원본 해시는 [manifest.json](manifest.json)에 기록했다.',
      '스크린샷은 SQLite 실행 결과를 표시한 문서 화면이며 DB 관리 도구의 화면이 아니다.', '',
      ...captures.flatMap(item => {
        const stem = path.basename(item.source, '.txt');
        return [`## ${stem.toUpperCase()}`, '', `[원본 SQL·결과 텍스트](../${stem}.txt)`, '',
          `![${stem.toUpperCase()} SQL 실행 결과](${stem}.png)`, ''];
      }),
    ];
    fs.writeFileSync(path.join(destination, 'README.md'), index.join('\n'), 'utf8');
    console.log(`Captured ${captures.length} result screenshots. No horizontal overflow.`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
