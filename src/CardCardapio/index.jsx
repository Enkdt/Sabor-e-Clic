import { PratoCardapio } from '../Assets/PratoCardapio'
import { formatCurrency } from '../utils/formatCurrency'
import './CardCardapio.css'
export const CardCardapio=({dishName,description,price})=>{
    return(
        <>
            <div className='CardCardapio'>
                <PratoCardapio/>
                <h2>{dishName}</h2>
                <p>{description}</p>
                <div className='cardCardapioFooter'>
                    <span className='cardCardapioPrice'>{formatCurrency(price)}</span>
                    <button type='button' onClick={(e)=>e.preventDefault()}>Adicionar</button>
                </div>
            </div>
        </>
    )
}
