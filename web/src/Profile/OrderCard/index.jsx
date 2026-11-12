import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { formatCurrency } from '../../utils/formatCurrency'
import { fetchReviews, submitReview } from '../../authSession'
import './OrderCard.css'

const STATUS_LABELS={ preparando:'Preparando', pronto:'Pronto', pago:'Pago', aguardando:'Aguardando pagamento', entregue:'Entregue', negado:'Cancelado' }

const ITEM_LABELS={ aguardando:'Aguardando confirmação', confirmado:'Confirmado', preparando:'Em preparo', pronto:'Pronto', entregue:'Entregue', negado:'Recusado' }

function formatDate(iso){
    if(!iso) return ''
    const [y,m,d]=iso.split('-')
    return d && m && y ? `${d}/${m}/${y}` : iso
}

function ItemReview({orderId, item, review, onReviewed}){
    const [open,setOpen]=useState(false)
    const [nota,setNota]=useState(5)
    const [comentario,setComentario]=useState('')
    const [saving,setSaving]=useState(false)
    const [error,setError]=useState('')

    const enviar=async (e)=>{
        e.preventDefault()
        if(saving) return
        setSaving(true); setError('')
        try{
            const saved=await submitReview(orderId,{ id_prato:item.id_prato, nota:Number(nota), comentario })
            onReviewed(saved)
            setOpen(false)
        }catch(err){
            setError(err.message)
        }finally{
            setSaving(false)
        }
    }

    return(
        <li>
            <div className='orderCardItemTop'>
                <span>{`${item.quantidade} × ${item.nome}`}</span>
                {item.restaurante_slug
                    ? <NavLink to={`/restaurante/${item.restaurante_slug}`} className='orderCardItemRestaurant'>{item.restaurante}</NavLink>
                    : <span className='orderCardItemRestaurant'>{item.restaurante}</span>}
                <span className={`orderCardItemStatus orderCardItemStatus--${item.status}`}>{ITEM_LABELS[item.status] || item.status}</span>
                {review
                    ? <span className='orderCardReviewed' role='status'>{`Avaliado: ${review.nota}★`}</span>
                    : item.status==='entregue' && !open && <button type='button' className='orderCardRate' onClick={()=>setOpen(true)}>Avaliar</button>}
            </div>
            {item.status==='negado' && item.motivo_negacao && (
                <p className='orderCardDenied'>{`Recusado pela cozinha: ${item.motivo_negacao}`}</p>
            )}
            {!review && open && (
                <form className='orderCardReviewForm' onSubmit={enviar}>
                    <label>Nota:
                        <select value={nota} onChange={(e)=>setNota(e.target.value)}>
                            {[5,4,3,2,1].map((n)=>(<option key={n} value={n}>{n}</option>))}
                        </select>
                    </label>
                    <label>Comentário (opcional):
                        <textarea value={comentario} maxLength={500} onChange={(e)=>setComentario(e.target.value)} rows={2}/>
                    </label>
                    {error && <p role='alert' className='orderCardReviewError'>{error}</p>}
                    <div className='orderCardReviewActions'>
                        <button type='submit' disabled={saving}>{saving ? 'Enviando…' : 'Enviar avaliação'}</button>
                        <button type='button' onClick={()=>setOpen(false)}>Cancelar</button>
                    </div>
                </form>
            )}
        </li>
    )
}

export const OrderCard=({order})=>{
    const label=STATUS_LABELS[order.status] || order.status
    const entregue=order.status==='entregue'
    const pago=order.pago

    const [reviews,setReviews]=useState([])

    useEffect(()=>{
        if(!pago) return
        let active=true
        fetchReviews(order.id)
            .then((r)=>{ if(active) setReviews(r) })
            .catch(()=>{}) // falha ao ler avaliações não deve quebrar o card
        return ()=>{ active=false }
    },[order.id,pago])

    const reviewFor=(idPrato)=>reviews.find((r)=>r.id_prato===idPrato) || null
    const addReview=(saved)=>setReviews((prev)=>[...prev.filter((r)=>r.id_prato!==saved.id_prato), saved])

    return(
        <div className='orderCard flex flex-col gap-4 sm:flex-row'>
            {/*Placeholder da imagem do restaurante*/}
            <div className='orderCardIcon'></div>
            <div className='orderCardInfo'>
                <p className='orderCardName'>{`Pedido #${order.id}`}</p>
                <p className='orderCardDate'>{formatDate(order.data)}</p>
                <p className='orderCardLabel'>Detalhes do pedido:</p>
                <ul className='orderCardItems'>
                    {order.itens.map((item)=>(
                        pago
                            ? <ItemReview key={item.id_prato} orderId={order.id} item={item} review={reviewFor(item.id_prato)} onReviewed={addReview}/>
                            : <li key={item.id_prato}><div className='orderCardItemTop'><span>{`${item.quantidade} × ${item.nome}`}</span>{item.restaurante_slug ? <NavLink to={`/restaurante/${item.restaurante_slug}`} className='orderCardItemRestaurant'>{item.restaurante}</NavLink> : <span className='orderCardItemRestaurant'>{item.restaurante}</span>}</div></li>
                    ))}
                </ul>
            </div>
            <div className='orderCardSide items-start sm:items-end'>
                <span className={`orderCardStatus ${entregue ? 'delivered' : ''}`}>{label}</span>
                <p className='orderCardTotal'>{formatCurrency(Number(order.total))}</p>
            </div>
        </div>
    )
}
