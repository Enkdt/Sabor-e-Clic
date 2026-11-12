import { NavLink } from 'react-router-dom'
import './StockItem.css'

const formatDate=(isoDate)=>isoDate ? isoDate.split('-').reverse().join('/') : ''
const formatQty=(q)=>{
    const n=Number(q)
    return Number.isInteger(n) ? String(n) : String(q)
}

export const StockItem=({item})=>{

    const soldOut=Number(item.quantidade)<=0

    return(
        <li className='stockItemWrapper'>
            {soldOut && <p className='stockItemAlert'>Produto esgotado!</p>}
            <div className={`stockItem flex flex-col gap-4 sm:flex-row ${soldOut ? 'soldOut' : ''}`}>
                {/*Imagem do produto (placeholder quando ausente)*/}
                <div className='stockItemImg w-full sm:w-[192px]' style={item.imagem ? { backgroundImage: `url(${item.imagem})` } : undefined}></div>
                <div className='stockItemInfo'>
                    <div className='stockItemTitle'>
                        <h2>{item.nome}</h2>
                    </div>
                    <p>{`Quantidade: ${formatQty(item.quantidade)} ${item.unidade}`}</p>
                    <p>{`Data validade: ${formatDate(item.validade)}`}</p>
                </div>
                <NavLink to={`/gerente/estoque/${item.id}/editar`} className='stockItemEdit'>Editar</NavLink>
            </div>
        </li>
    )
}
