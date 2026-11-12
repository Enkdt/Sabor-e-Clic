import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { CaretDownIcon } from '@phosphor-icons/react'
import { fetchIngredients } from '../../authSession'
import { Header } from '../../Components/Header'
import { NextBtn } from '../../Components/NextBtn'
import { StockItem } from './StockItem'
import './Stock.css'

const sortFunctions={
    '': ()=>0,
    nome: (a,b)=>a.nome.localeCompare(b.nome),
    quantidade: (a,b)=>Number(a.quantidade)-Number(b.quantidade),
    validade: (a,b)=>a.validade.localeCompare(b.validade)
}

export const Stock=()=>{

    const [sortBy,setSortBy]=useState('')
    const [items,setItems]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error

    useEffect(()=>{
        let active=true
        fetchIngredients()
            .then((list)=>{ if(active){ setItems(list); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    const sortedList=[...items].sort(sortFunctions[sortBy])

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
                        <p className='text-[20px] md:text-[26px]'>{`${items.length} Produtos no estoque`}</p>
                        <label className='stockSort'>
                            <select className='text-[20px] md:text-[26px]' value={sortBy} onChange={(e)=>setSortBy(e.target.value)} aria-label='Ordenar por'>
                                <option value='' disabled>Ordenar por</option>
                                <option value='nome'>Nome</option>
                                <option value='quantidade'>Quantidade</option>
                                <option value='validade'>Validade</option>
                            </select>
                            <CaretDownIcon className='stockSortIcon'/>
                        </label>
                    </div>

                    {status==='loading' && <p role='status'>Carregando estoque…</p>}
                    {status==='error' && <p role='alert'>Não foi possível carregar o estoque.</p>}
                    {status==='ready' && items.length===0 && <p>Nenhum item no estoque ainda.</p>}
                    {status==='ready' && (
                        <ul className='stockList'>
                            {sortedList.map((item)=>(
                                <StockItem key={item.id} item={item}/>
                            ))}
                        </ul>
                    )}
                </section>
            </div>
        </main>
    )
}
