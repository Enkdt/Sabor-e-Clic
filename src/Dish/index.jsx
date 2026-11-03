import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { dishesList } from '../data/dishesData'
import { formatCurrency } from '../utils/formatCurrency'
import { Header } from '../Components/Header'
import { NextBtn } from '../Components/NextBtn'
import './Dish.css'
export const Dish=()=>{

    const { id }=useParams()
    const [quantity,setQuantity]=useState(1)
    const dish=dishesList.find((item)=>item.id===Number(id))

    if(!dish){
        return(
            <main className='dishPage'>
                <h1>Prato não encontrado :/</h1>
                <Link to='/'>Voltar para o início</Link>
            </main>
        )
    }

    return(
        <main className='dishPage'>
            <Header/>
            {/*Placeholder da imagem do prato*/}
            <section className='dishPageImg h-[200px] md:h-[320px]'></section>

            <section className='dishPageInfo px-4'>
                <h1 className='dishPageName text-[32px] md:text-[40px]'>{dish.name}</h1>
                <p className='dishPageDescription'>{dish.description}</p>
            </section>

            <section className='dishPageDetails grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-[64px] px-4'>
                <div className='dishPageIngredients'>
                    <h2>Ingredientes:</h2>
                    <ul>
                        {dish.ingredients.map((ingredient)=>(
                            <li key={ingredient}>{ingredient}</li>
                        ))}
                    </ul>
                </div>

                <div className='dishPagePurchase'>
                    <p className='dishPagePrice'>{formatCurrency(dish.price)}</p>
                    <label className='dishPageQuantity'>
                        <span>Quantidade:</span>
                        <input
                            type='number'
                            min='1'
                            value={quantity}
                            onChange={(e)=>setQuantity(Math.max(1,Number(e.target.value)||1))}
                        />
                    </label>
                    <NextBtn text='Adicionar ao carrinho'/>
                </div>
            </section>
        </main>
    )
}
