import { formatCurrency } from '../../utils/formatCurrency'
import './OrderCard.css'
export const OrderCard=({order})=>{
    return(
        <div className='orderCard flex flex-col gap-4 sm:flex-row'>
            {/*Placeholder da imagem do restaurante*/}
            <div className='orderCardIcon'></div>
            <div className='orderCardInfo'>
                <p className='orderCardName'>{order.restaurantName}</p>
                <p className='orderCardDate'>{order.date}</p>
                <p className='orderCardLabel'>Detalhes do pedido:</p>
                <ul className='orderCardItems'>
                    {order.items.map((item)=>(
                        <li key={item}>{item}</li>
                    ))}
                </ul>
            </div>
            <div className='orderCardSide items-start sm:items-end'>
                <span className={`orderCardStatus ${order.status==='Entregue' ? 'delivered' : ''}`}>{order.status}</span>
                <p className='orderCardTotal'>{formatCurrency(order.total)}</p>
                {order.status==='Entregue' && <button type='button' className='orderCardRate'>Avaliar</button>}
            </div>
        </div>
    )
}
