import './NextBtn.css'
// type padrão 'submit' para não quebrar os botões que enviam formulários (Login, Cadastro).
// Passe type='button' quando o botão só dispara um onClick fora de um <form>.
export const NextBtn=({text,onClick,type='submit',disabled=false})=>{
    return <button type={type} onClick={onClick} disabled={disabled} className='nextBtn w-full max-w-[360pxz]'>{text}</button>
}
