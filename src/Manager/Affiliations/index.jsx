import { useEffect, useState } from 'react'
import { fetchCooks, fetchRestaurants, affiliateCook, unaffiliateCook } from '../../authSession'
import { Header } from '../../Components/Header'
import './Affiliations.css'

export const Affiliations=()=>{
    const [cooks,setCooks]=useState([])
    const [restaurantes,setRestaurantes]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error
    const [erro,setErro]=useState('')

    useEffect(()=>{
        let active=true
        Promise.all([fetchCooks(), fetchRestaurants()])
            .then(([c,r])=>{ if(active){ setCooks(c); setRestaurantes(r); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    const atualizar=(coz)=>setCooks((prev)=>prev.map((c)=>c.id_usuario===coz.id_usuario ? coz : c))

    const filiar=async (idUsuario, idRestaurante)=>{
        if(!idRestaurante) return
        setErro('')
        try{ atualizar(await affiliateCook(idUsuario, Number(idRestaurante))) }
        catch(err){ setErro(err.message) }
    }
    const desfiliar=async (idUsuario, idRestaurante)=>{
        setErro('')
        try{ atualizar(await unaffiliateCook(idUsuario, idRestaurante)) }
        catch(err){ setErro(err.message) }
    }

    return(
        <main className='affPage'>
            <Header/>
            <div className='affContent'>
                <h1>Filiação de cozinheiros</h1>
                <p className='affHint'>Associe cada cozinheiro aos restaurantes que ele poderá gerenciar.</p>
                {erro && <p role='alert' className='affError'>{erro}</p>}
                {status==='loading' && <p role='status'>Carregando…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os dados.</p>}
                {status==='ready' && cooks.length===0 && <p className='affHint'>Nenhum cozinheiro cadastrado ainda.</p>}

                <ul className='affList'>
                    {cooks.map((c)=>(
                        <li key={c.id_usuario} className='affItem'>
                            <div className='affWho'>
                                <strong>{c.nome}</strong>
                                <span>{c.email}</span>
                            </div>
                            <div className='affRestaurants'>
                                {c.restaurantes.length===0 && <span className='affHint'>Sem restaurantes.</span>}
                                {c.restaurantes.map((r)=>(
                                    <span key={r.id} className='affChip'>
                                        {r.nome}
                                        <button type='button' aria-label={`Remover ${r.nome}`} onClick={()=>desfiliar(c.id_usuario,r.id)}>×</button>
                                    </span>
                                ))}
                            </div>
                            <select defaultValue='' onChange={(e)=>{ filiar(c.id_usuario, e.target.value); e.target.value='' }}>
                                <option value='' disabled>+ Filiar a restaurante…</option>
                                {restaurantes
                                    .filter((r)=>!c.restaurantes.some((cr)=>cr.id===r.id))
                                    .map((r)=>(<option key={r.id} value={r.id}>{r.nome}</option>))}
                            </select>
                        </li>
                    ))}
                </ul>
            </div>
        </main>
    )
}
