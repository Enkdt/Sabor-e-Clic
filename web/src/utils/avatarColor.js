// Gera cor e iniciais determinísticas a partir de um nome, para avatares padrão
// (sem depender de geração de imagem no servidor; funciona no serverless também).

// Paleta de fundos com contraste suficiente para texto branco (derivada do verde
// da marca + tons análogos sóbrios).
const PALETTE = ['#426700', '#5a4a2a', '#7a1f4b', '#1f5a7a', '#6a1f7a', '#2f7a3f', '#8a5a00']

export function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function colorFor(name) {
  const s = String(name || '')
  let hash = 0
  for (let i = 0; i < s.length; i++) hash = (hash * 31 + s.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
}
