import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { CaretDownIcon } from '@phosphor-icons/react'
import { stockList } from '../../data/stockData'
import { Header } from '../../Components/Header'
import { NextBtn } from '../../Components/NextBtn'
import { StockItem } from './StockItem'
import './Stock.css'

const sortFunctions={
    '': ()=>0,
    name: (a,b)=>a.name.localeCompare(b.name),
    quantity: (a,b)=>a.quantity-b.quantity,
    expiresAt: (a,b)=>a.expiresAt.localeCompare(b.expiresAt)
}

export const Stock=()=>{

    const [sortBy,setSortBy]=useState('')

    const sortedList=[...stockList].sort(sortFunctions[sortBy])

    return(
        <main className='stockPage'>
            <Header/>
            <div className='stockContent max-w-[1390px] mx-auto px-4'>
                <div className='stockTop flex flex-col gap-4 md:flex-row md:items-center md:justify-between'>
                    <h1 className='text-[32px] md:text-[36px]'>Estoque</h1>
                    <NavLink to='/gerente/estoque/adicionar' className='block w-full md:w-[380px]'>
                        <NextBtn text='Adicionar'/>
                    </NavLink>
                </div>

                <section className='stockBox px-4 py-6 md:px-8 lg:px-16 xl:px-[170px]'>
                    <div className='stockBoxHeader'>
                        <p className='text-[20px] md:text-[26px]'>{`${stockList.length} Produtos no estoque`}</p>
                        <label className='stockSort'>
                            <select className='text-[20px] md:text-[26px]' value={sortBy} onChange={(e)=>setSortBy(e.target.value)} aria-label='Ordenar por'>
                                <option value='' disabled>Ordenar por</option>
                                <option value='name'>Nome</option>
                                <option value='quantity'>Quantidade</option>
                                <option value='expiresAt'>Validade</option>
                            </select>
                            <CaretDownIcon className='stockSortIcon'/>
                        </label>
                    </div>

                    <ul className='stockList'>
                        {sortedList.map((item)=>(
                            <StockItem key={item.id} item={item}/>
                        ))}
                    </ul>
                </section>
            </div>
        </main>
    )
}
