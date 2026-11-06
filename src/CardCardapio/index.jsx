import { useState } from 'react'
import { PratoCardapio } from '../Assets/PratoCardapio'
import { formatCurrency } from '../utils/formatCurrency'
import { useCart } from '../cartContext'
import './CardCardapio.css'
export const CardCardapio=({id,dishName,description,price,image})=>{
    const { addItem }=useCart()
    const [added,setAdded]=useState(false)

    const handleAdd=(e)=>{
        // O card está dentro de um NavLink; impede a navegação ao adicionar ao carrinho.
        e.preventDefault()
        e.stopPropagation()
        addItem({ id_prato: id, nome: dishName, preco: Number(price), quantity: 1, imagem: image })
        setAdded(true)
    }

    return(
        <>
            <div className='CardCardapio'>
                {image
                    ? <img className='cardCardapioImg' src={image} alt={dishName}/>
                    : <PratoCardapio/>}
                <h2>{dishName}</h2>
                <p>{description}</p>
                <div className='cardCardapioFooter'>
                    <span className='cardCardapioPrice'>{formatCurrency(price)}</span>
                    <button type='button' onClick={handleAdd}>Adicionar</button>
                    <span className='cardCardapioFeedback' role='status' aria-live='polite'>
                        {added ? `${dishName} adicionado ao carrinho.` : ''}
                    </span>
                </div>
            </div>
        </>
    )
}
