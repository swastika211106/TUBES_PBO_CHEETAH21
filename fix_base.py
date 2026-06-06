with open('base.html', 'r', encoding='utf-8') as f:
    base = f.read()

# Revert the global accidental replacement
base = base.replace('align-items: flex-start; justify-content: center; padding-top: 80px;', 'align-items: center; justify-content: center;')

# Now selectively apply ONLY to .modal-overlay
target = '.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.6); backdrop-filter: blur(4px); z-index: 1000; display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s ease; }'
replacement = '.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.6); backdrop-filter: blur(4px); z-index: 1000; display: none; align-items: flex-start; justify-content: center; padding-top: 80px; opacity: 0; transition: opacity 0.3s ease; }'

base = base.replace(target, replacement)

with open('base.html', 'w', encoding='utf-8') as f:
    f.write(base)
