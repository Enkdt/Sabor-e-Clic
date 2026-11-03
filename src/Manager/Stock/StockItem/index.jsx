import './StockItem.css'
const formatDate=(isoDate)=>isoDate.split('-').reverse().join('/')
export const StockItem=({item})=>{

    const soldOut=item.quantity===0

    return(
        <li className='stockItemWrapper'>
            {soldOut && <p className='stockItemAlert'>Produto esgotado!</p>}
            <div className={`stockItem flex flex-col gap-4 sm:flex-row ${soldOut ? 'soldOut' : ''}`}>
                {/*Placeholder da imagem do produto*/}
                <div className='stockItemImg w-full sm:w-[192px]'></div>
                <div className='stockItemInfo'>
                    <div className='stockItemTitle'>
                        <h2>{item.name}</h2>
                        <span className='stockItemTag'>{item.category}</span>
                    </div>
                    <p>{`Quantidade: ${item.quantity}${item.unit}`}</p>
                    <p>{`Data adição: ${formatDate(item.addedAt)}`}</p>
                    <p>{`Data validade: ${formatDate(item.expiresAt)}`}</p>
                </div>
                <button type='button' className='stockItemEdit'>Editar</button>
            </div>
        </li>
    )
}
