import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { formatCurrency } from '../utils/formatCurrency'
import { fetchDishReviews } from '../authSession'
import { useCart } from '../cartContext'
import { Header } from '../Components/Header'
import { NextBtn } from '../Components/NextBtn'
import './Dish.css'

function formatDate(iso){
    if(!iso) return ''
    const d=new Date(iso)
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('pt-BR')
}

export const Dish=()=>{

    const { slugRest, slugPrato }=useParams()
    const [quantity,setQuantity]=useState(1)
    const [dish,setDish]=useState(null)
    const [status,setStatus]=useState('loading')
    const [added,setAdded]=useState(false)
    const [reviews,setReviews]=useState(null) // { media, total, avaliacoes }
    const { addItem }=useCart()

    useEffect(() => {
        let active = true
        fetch(`/api/restaurantes/${encodeURIComponent(slugRest)}/pratos/${encodeURIComponent(slugPrato)}`)
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Prato não encontrado.')
                return data.prato
            })
            .then((item) => { if (active) { setDish(item); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [slugRest, slugPrato])

    useEffect(() => {
        if (!dish) return
        let active = true
        fetchDishReviews(dish.id).then((r) => { if (active) setReviews(r) }).catch(() => {})
        return () => { active = false }
    }, [dish])

    if(status === 'loading'){
        return <main className='dishPage'><Header/><p>Carregando prato…</p></main>
    }
    if(status === 'error' || !dish){
        return(
            <main className='dishPage'>
                <Header/>
                <h1>Prato não encontrado :/</h1>
                <Link to='/'>Voltar para o início</Link>
            </main>
        )
    }

    return(
        <main className='dishPage'>
            <Header/>
            {/*Imagem do prato (gradiente placeholder quando ausente)*/}
            <section className='dishPageImg h-[200px] md:h-[320px]' style={dish.imagem ? { backgroundImage: `url(${dish.imagem})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}></section>

            <section className='dishPageInfo px-4'>
                <h1 className='dishPageName text-[32px] md:text-[40px]'>{dish.nome}</h1>
                {reviews && reviews.total > 0 && (
                    <p className='dishPageRatingSummary'>{`★ ${reviews.media} · ${reviews.total} avaliação${reviews.total === 1 ? '' : 'es'}`}</p>
                )}
                {dish.descricao && <p className='dishPageDescription'>{dish.descricao}</p>}
            </section>

            {/* Grupo com as 3 divs: categorias | ingredientes | preço + adicionar */}
            <section className='dishPageDetails px-4'>
                <div className='dishPageGroup grid grid-cols-1 md:grid-cols-3 gap-8'>
                    <div className='dishPageBlock dishPageCategories'>
                        <h2>Categorias</h2>
                        {dish.categorias.length ? (
                            <ul>{dish.categorias.map((c)=>(<li key={c}>{c}</li>))}</ul>
                        ) : <p className='dishPageEmpty'>Sem categorias.</p>}
                    </div>

                    <div className='dishPageBlock dishPageIngredients'>
                        <h2>Ingredientes</h2>
                        {dish.ingredientes.length ? (
                            <ul>{dish.ingredientes.map((i)=>(<li key={i.id_ingrediente}>{`${i.qtd} ${i.unidade_medida} · ${i.nome}`}</li>))}</ul>
                        ) : <p className='dishPageEmpty'>Sem ingredientes cadastrados.</p>}
                    </div>

                    <div className='dishPageBlock dishPagePurchase'>
                        <p className='dishPagePrice'>{formatCurrency(Number(dish.preco))}</p>
                        <label className='dishPageQuantity'>
                            <span>Quantidade:</span>
                            <input
                                type='number'
                                min='1'
                                value={quantity}
                                onChange={(e)=>setQuantity(Math.max(1,Number(e.target.value)||1))}
                            />
                        </label>
                        <NextBtn type='button' text='Adicionar ao carrinho' onClick={()=>{ addItem({ id_prato: dish.id, nome: dish.nome, preco: Number(dish.preco), quantity, imagem: dish.imagem }); setAdded(true) }}/>
                        <p className='dishPageFeedback' role='status' aria-live='polite'>
                            {added ? `${quantity} × ${dish.nome} adicionado ao carrinho.` : ''}
                        </p>
                    </div>
                </div>
            </section>

            {/* Seção de avaliações, abaixo do grupo, em outra div */}
            <section className='dishPageReviews px-4'>
                <h2>Avaliações</h2>
                {!reviews && <p className='dishPageEmpty'>Carregando avaliações…</p>}
                {reviews && reviews.total === 0 && <p className='dishPageEmpty'>Este prato ainda não tem avaliações.</p>}
                {reviews && reviews.total > 0 && (
                    <ul className='dishPageReviewList'>
                        {reviews.avaliacoes.map((a,idx)=>(
                            <li key={idx} className='dishPageReview'>
                                <div className='dishPageReviewHead'>
                                    <span className='dishPageReviewStars'>{'★'.repeat(a.nota)}{'☆'.repeat(5-a.nota)}</span>
                                    <span className='dishPageReviewDate'>{formatDate(a.criado_em)}</span>
                                </div>
                                <p className='dishPageReviewAuthor'>{a.cliente || 'Cliente'}</p>
                                {a.comentario && <p className='dishPageReviewText'>{a.comentario}</p>}
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </main>
    )
}
