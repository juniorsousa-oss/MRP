from pathlib import Path

p = Path('app_mrp.py')
s = p.read_text(encoding='utf-8')
marker = '      [data-testid="stSidebar"] {{border-right: 1px solid rgba(0,0,0,.08); }}'
css = '''      [data-testid="stSidebar"] {{border-right: 1px solid rgba(0,0,0,.08); }}
      /* Upload compacto: restaura o formato horizontal anterior sem alterar a lógica dos arquivos. */
      [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
        min-height: 40px !important;
        height: 40px !important;
        padding: 4px 8px !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
        border-radius: 6px !important;
      }}
      [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] > div {{
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
      }}
      [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
        margin: 0 !important;
      }}
      [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {{
        display: none !important;
      }}
      [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > div:nth-child(2) {{
        margin: 0 !important;
        padding: 0 !important;
        font-size: 0.72rem !important;
        line-height: 1.1 !important;
        white-space: nowrap !important;
      }}
      [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {{
        flex: 0 0 auto !important;
        min-height: 30px !important;
        height: 30px !important;
        padding: 0 10px !important;
        margin: 0 !important;
      }}
      [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] svg {{
        width: 13px !important;
        height: 13px !important;
      }}'''

if '/* Upload compacto: restaura o formato horizontal anterior' in s:
    raise SystemExit('O ajuste de upload já está aplicado.')
if marker not in s:
    raise SystemExit('Marcador CSS esperado não encontrado; nenhuma alteração aplicada.')
s = s.replace(marker, css, 1)
p.write_text(s, encoding='utf-8')
