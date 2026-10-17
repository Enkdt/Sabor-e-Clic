import { PratoCardapio } from '../Assets/PratoCardapio'
import './CardCardapio.css'
export const CardCardapio=()=>{
    return(
        <>
            <div className='CardCardapio'>
                <PratoCardapio/>
                <h2>Comida Gostosa</h2>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam suscipit volutpat nulla. Nulla blandit odio eget leo </p>
                <button>Adicionar ao carrinho</button>
            </div>
        </>
    )
}