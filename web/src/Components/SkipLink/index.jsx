import './SkipLink.css'

// ID do alvo do skip link; as páginas marcam seu <main> com este id.
export const CONTEUDO_PRINCIPAL_ID = 'conteudo-principal'

// Link "Pular para o conteúdo" para pessoas com baixa visão / usuários de teclado
// e leitores de tela. Invisível até receber foco (primeiro Tab da página); ao ser
// ativado, move o foco para o conteúdo principal (<main id="conteudo-principal">).
export const SkipLink=({ target = CONTEUDO_PRINCIPAL_ID })=>{
    const irParaConteudo=(e)=>{
        const alvo=document.getElementById(target)
        if(alvo){
            e.preventDefault()
            // tabindex=-1 permite focar um elemento não-interativo programaticamente.
            alvo.setAttribute('tabindex', '-1')
            alvo.focus()
            alvo.scrollIntoView()
        }
    }
    return (
        <a href={`#${target}`} className='skipLink' onClick={irParaConteudo}>
            Pular para o conteúdo
        </a>
    )
}
