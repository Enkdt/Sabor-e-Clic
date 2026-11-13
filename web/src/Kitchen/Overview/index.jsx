import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../authContext'
import { fetchRestaurant, fetchKitchenOrders } from '../../authSession'
import { Header } from '../../Components/Header'
import './Overview.css'

// Visão do cozinheiro: a quais restaurantes está filiado, com um resumo de cada um
// e um atalho para gerir os pratos. Equivalente ao painel do admin, no escopo do cozinheiro.
export const KitchenOverview=()=>{
    const { user }=useAuth()
    const restaurantes=user?.restaurantes || []
    const [detalhes,setDetalhes]=useState({}) // id -> { pratos, loading }
    const [fila,setFila]=useState(null) // nº de pedidos em preparo

    useEffect(()=>{
        let active=true
        Promise.all(restaurantes.map((r)=>fetchRestaurant(r.id).catch(()=>null)))
            .then((lista)=>{
                if(!active) return
                const mapa={}
                lista.forEach((r)=>{ if(r) mapa[r.id]=r })
                setDetalhes(mapa)
            })
        fetchKitchenOrders().then((p)=>{ if(active) setFila(p.length) }).catch(()=>{})
        return ()=>{ active=false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    },[user])

    return(
        <main id='conteudo-principal' className='kitchenOverviewPage'>
            <Header/>
            <div className='kitchenOverviewContent'>
                <h1>Minhas cozinhas</h1>
                <p className='kitchenOverviewSub'>Olá, {user?.nome?.split(' ')[0]}. Estes são os restaurantes sob sua gestão.</p>

                {fila!=null && (
                    <NavLink to='/cozinha' className='kitchenOverviewQueue'>
                        <span className='kitchenOverviewQueueNum'>{fila}</span>
                        <span>pedido{fila===1 ? '' : 's'} em preparo — abrir a cozinha</span>
                    </NavLink>
                )}

                {restaurantes.length===0 && (
                    <p className='kitchenOverviewEmpty'>
                        Você ainda não está filiado a nenhum restaurante. Um administrador precisa filiá-lo antes de você gerenciar pratos.
                    </p>
                )}

                <ul className='kitchenOverviewGrid'>
                    {restaurantes.map((r)=>{
                        const d=detalhes[r.id]
                        return(
                            <li key={r.id} className='kitchenOverviewCard'>
                                <div className='kitchenOverviewCardImg' style={d?.imagem ? { backgroundImage:`url(${d.imagem})` } : undefined}></div>
                                <div className='kitchenOverviewCardBody'>
                                    <h2>{r.nome}</h2>
                                    <p className='kitchenOverviewStat'>
                                        {d ? `${d.pratos.length} prato${d.pratos.length===1 ? '' : 's'} no cardápio` : 'Carregando…'}
                                    </p>
                                    <div className='kitchenOverviewLinks'>
                                        <NavLink to='/cozinha/pratos'>Gerenciar pratos</NavLink>
                                        {r.slug && <NavLink to={`/restaurante/${r.slug}`}>Ver página</NavLink>}
                                    </div>
                                </div>
                            </li>
                        )
                    })}
                </ul>
            </div>
        </main>
    )
}
