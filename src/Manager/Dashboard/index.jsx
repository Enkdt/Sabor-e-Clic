import { useEffect, useState } from 'react'
import { CaretDownIcon } from '@phosphor-icons/react'
import { fetchDashboard } from '../../authSession'
import { formatCurrency } from '../../utils/formatCurrency'
import { Header } from '../../Components/Header'
import { KpiCard } from './KpiCard'
import { ChartCard } from './ChartCard'
import './Dashboard.css'

const PERIODOS=[
    { value:'30', label:'Últimos 30 dias' },
    { value:'7', label:'Últimos 7 dias' },
    { value:'90', label:'Últimos 90 dias' },
]

// Monta escala/máximo de um gráfico a partir dos valores reais.
function buildChart(title,subtitle,badge,points,format){
    const max=Math.max(1,...points.map((p)=>Number(p.value)))
    const ticks=4
    const scale=Array.from({length:ticks+1},(_,i)=>format(max*(ticks-i)/ticks))
    return { title, subtitle, badge, max, scale, bars: points.map((p)=>({ label:p.label, value:Number(p.value) })) }
}

function toCsv(data){
    const rows=[
        ['Métrica','Valor'],
        ['Receita total', data.kpis.receita_total],
        ['Pedidos pagos', data.kpis.pedidos_pagos],
        ['Pedidos no período', data.kpis.pedidos_total],
        ['Ticket médio', data.kpis.ticket_medio],
        ['Itens em estoque', data.kpis.itens_estoque],
        ['Itens sem estoque', data.kpis.itens_sem_estoque],
        [],
        ['Dia','Vendas'],
        ...data.vendas_por_dia.map((d)=>[d.label,d.value]),
        [],
        ['Restaurante','Receita'],
        ...data.receita_por_restaurante.map((r)=>[r.label,r.value]),
    ]
    return rows.map((r)=>r.join(',')).join('\n')
}

export const Dashboard=()=>{
    const [periodo,setPeriodo]=useState('30')
    const [data,setData]=useState(null)
    const [status,setStatus]=useState('loading') // loading | ready | error

    useEffect(()=>{
        let active=true
        fetchDashboard(periodo)
            .then((d)=>{ if(active){ setData(d); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[periodo])

    const exportar=()=>{
        if(!data) return
        const blob=new Blob([toCsv(data)],{ type:'text/csv;charset=utf-8;' })
        const url=URL.createObjectURL(blob)
        const link=document.createElement('a')
        link.href=url
        link.download=`dashboard-${periodo}dias.csv`
        link.click()
        URL.revokeObjectURL(url)
    }

    const salesChart=data && buildChart('Quantidade de vendas','Pedidos por dia da semana no período','', data.vendas_por_dia, (v)=>String(Math.round(v)))
    const revenueChart=data && buildChart('Receita por restaurante','Faturamento de pedidos pagos','', data.receita_por_restaurante, (v)=>formatCurrency(v))

    return(
        <main className='dashboardPage'>
            <Header/>
            <div className='dashboardContent max-w-[1180px] mx-auto px-4'>
                <div className='dashboardTop flex flex-col gap-4 md:flex-row md:items-end md:justify-between'>
                    <div>
                        <h1 className='text-[32px] md:text-[40px]'>Dashboard analítico</h1>
                        <p className='dashboardSubtitle'>Acompanhe vendas e desempenho dos restaurantes.</p>
                    </div>
                    {data && <span className='dashboardPeriod'>{`Período: ${data.periodo.inicio} a ${data.periodo.fim}`}</span>}
                </div>

                <div className='dashboardFilters flex flex-col gap-3 sm:flex-row sm:flex-wrap'>
                    <div className='dashboardSelect'>
                        <select aria-label='Período' value={periodo} onChange={(e)=>setPeriodo(e.target.value)}>
                            {PERIODOS.map((option)=>(
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                        <CaretDownIcon className='dashboardSelectIcon'/>
                    </div>
                    {/* Região e categoria não têm dado no domínio atual; desabilitados até existir. */}
                    <div className='dashboardSelect'>
                        <select aria-label='Região' disabled title='Indisponível: sem dados de região'>
                            <option>Todas as regiões</option>
                        </select>
                        <CaretDownIcon className='dashboardSelectIcon'/>
                    </div>
                    <button type='button' className='dashboardExport' onClick={exportar} disabled={status!=='ready'}>Exportar relatório</button>
                </div>

                {status==='loading' && <p role='status'>Carregando métricas…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar o painel.</p>}

                {status==='ready' && data && <>
                    <div className='dashboardKpis grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4'>
                        <KpiCard label='Receita total' badge={`${data.kpis.pedidos_pagos} pagos`} value={formatCurrency(Number(data.kpis.receita_total))} note='Soma dos pedidos pagos no período'/>
                        <KpiCard label='Pedidos no período' badge={`${data.kpis.pedidos_pagos} pagos`} value={String(data.kpis.pedidos_total)} note='Todos os pedidos no período'/>
                        <KpiCard label='Ticket médio' badge='pagos' value={formatCurrency(Number(data.kpis.ticket_medio))} note='Receita ÷ pedidos pagos'/>
                        <KpiCard label='Itens em estoque' badge={`${data.kpis.itens_sem_estoque} esgotados`} value={String(data.kpis.itens_estoque)} note='Ingredientes cadastrados'/>
                    </div>

                    <div className='dashboardCharts grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4'>
                        <ChartCard {...salesChart}/>
                        <ChartCard {...revenueChart}/>
                    </div>
                </>}
            </div>
        </main>
    )
}
