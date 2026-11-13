import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { CaretDownIcon } from '@phosphor-icons/react'
import { fetchRestaurants, fetchRestaurantMetrics } from '../../authSession'
import { formatCurrency } from '../../utils/formatCurrency'
import { Header } from '../../Components/Header'
import { KpiCard } from '../Dashboard/KpiCard'
import { ChartCard } from '../Dashboard/ChartCard'
import '../Dashboard/Dashboard.css'

const PERIODOS=[
    { value:'30', label:'Últimos 30 dias' },
    { value:'7', label:'Últimos 7 dias' },
    { value:'90', label:'Últimos 90 dias' },
]

// Monta escala/máximo de um gráfico a partir dos valores reais (mesmo padrão do Dashboard global).
function buildChart(title,subtitle,badge,points,format){
    const max=Math.max(1,...points.map((p)=>Number(p.value)))
    const ticks=4
    const scale=Array.from({length:ticks+1},(_,i)=>format(max*(ticks-i)/ticks))
    return { title, subtitle, badge, max, scale, bars: points.map((p)=>({ label:p.label, value:Number(p.value) })) }
}

// Mini dashboard escopado a um restaurante. O backend (metricas_restaurante) faz o
// gate de ownership: admin vê qualquer um, cozinheiro só os que gerencia.
export const RestaurantMetrics=()=>{
    const { id } = useParams()
    const navigate = useNavigate()
    const [restaurantes,setRestaurantes]=useState([])
    const [periodo,setPeriodo]=useState('30')
    const [data,setData]=useState(null)
    const [status,setStatus]=useState('loading') // loading | ready | error

    // Lista de restaurantes para o seletor (e para resolver o id inicial).
    useEffect(()=>{
        let active=true
        fetchRestaurants()
            .then((lista)=>{ if(active) setRestaurantes(lista) })
            .catch(()=>{ /* o seletor só fica vazio; a métrica ainda carrega pelo id da URL */ })
        return ()=>{ active=false }
    },[])

    // Carrega as métricas do restaurante selecionado no período escolhido.
    // Sem id, não há fetch — o estado "vazio" é derivado de `id`, não de setState
    // no corpo do effect (evita react-hooks/set-state-in-effect).
    useEffect(()=>{
        if(!id) return
        let active=true
        fetchRestaurantMetrics(id,periodo)
            .then((d)=>{ if(active){ setData(d); setStatus('ready') } })
            .catch(()=>{ if(active){ setData(null); setStatus('error') } })
        return ()=>{ active=false }
    },[id,periodo])

    const trocarRestaurante=(novoId)=>{
        if(novoId) navigate(`/gerente/restaurantes/${novoId}/metricas`)
    }

    const vazio=!id
    // Os dados correspondem ao restaurante atual? (evita mostrar o anterior ao trocar).
    const dadosDoAtual=data && String(data.restaurante?.id)===String(id)
    const salesChart=data && buildChart('Quantidade de vendas','Pedidos por dia da semana no período','', data.vendas_por_dia, (v)=>String(Math.round(v)))
    const dishesChart=data && buildChart('Receita por prato','Faturamento de pedidos pagos deste restaurante','', data.receita_por_prato, (v)=>formatCurrency(v))

    return(
        <main id='conteudo-principal' className='dashboardPage'>
            <Header/>
            <div className='dashboardContent max-w-[1180px] mx-auto px-4'>
                <div className='dashboardTop flex flex-col gap-4 md:flex-row md:items-end md:justify-between'>
                    <div>
                        <h1 className='text-[32px] md:text-[40px]'>Métricas por restaurante</h1>
                        <p className='dashboardSubtitle'>
                            {data?.restaurante?.nome
                                ? `Desempenho de ${data.restaurante.nome}.`
                                : 'Selecione um restaurante para ver o desempenho.'}
                        </p>
                    </div>
                    {data && <span className='dashboardPeriod'>{`Período: ${data.periodo.inicio} a ${data.periodo.fim}`}</span>}
                </div>

                <div className='dashboardFilters flex flex-col gap-3 sm:flex-row sm:flex-wrap'>
                    <div className='dashboardSelect'>
                        <select
                            aria-label='Restaurante'
                            value={id || ''}
                            onChange={(e)=>trocarRestaurante(e.target.value)}
                        >
                            <option value='' disabled>Selecione um restaurante</option>
                            {restaurantes.map((r)=>(
                                <option key={r.id} value={r.id}>{r.nome}</option>
                            ))}
                        </select>
                        <CaretDownIcon className='dashboardSelectIcon'/>
                    </div>
                    <div className='dashboardSelect'>
                        <select aria-label='Período' value={periodo} onChange={(e)=>setPeriodo(e.target.value)} disabled={!id}>
                            {PERIODOS.map((option)=>(
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                        <CaretDownIcon className='dashboardSelectIcon'/>
                    </div>
                </div>

                {vazio && <p role='status'>Escolha um restaurante no seletor acima.</p>}
                {!vazio && status!=='error' && !dadosDoAtual && <p role='status'>Carregando métricas…</p>}
                {!vazio && status==='error' && <p role='alert'>Não foi possível carregar as métricas deste restaurante.</p>}

                {!vazio && status==='ready' && dadosDoAtual && <>
                    <div className='dashboardKpis grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4'>
                        <KpiCard label='Receita do restaurante' badge={`${data.kpis.pedidos_pagos} pagos`} value={formatCurrency(Number(data.kpis.receita_total))} note='Soma das linhas pagas deste restaurante'/>
                        <KpiCard label='Pedidos pagos' badge='no período' value={String(data.kpis.pedidos_pagos)} note='Pedidos pagos com itens deste restaurante'/>
                        <KpiCard label='Itens vendidos' badge='unidades' value={String(data.kpis.itens_vendidos)} note='Quantidade de pratos vendidos'/>
                        <KpiCard label='Ticket médio' badge='pagos' value={formatCurrency(Number(data.kpis.ticket_medio))} note='Receita ÷ pedidos pagos'/>
                        <KpiCard label='Pratos cadastrados' badge={`${data.kpis.pratos_indisponiveis} indisponíveis`} value={String(data.kpis.pratos_total)} note='Pratos do restaurante'/>
                    </div>

                    <div className='dashboardCharts grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4'>
                        <ChartCard {...salesChart}/>
                        {data.receita_por_prato.length > 0
                            ? <ChartCard {...dishesChart}/>
                            : <section className='chartCard'><p className='chartCardSubtitle'>Sem vendas de pratos no período.</p></section>}
                    </div>
                </>}
            </div>
        </main>
    )
}
