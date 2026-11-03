export const dashboardPeriod = '01/09/2026 a 02/10/2026'

export const dashboardKpis = [
    { id: 1, label: 'Receita total', badge: '+12,4%', value: 'R$ 284.900', note: '3.842 pedidos concluídos' },
    { id: 2, label: 'Pedidos concluídos', badge: '+8,1%', value: '3.842', note: '98,4% taxa de entrega no prazo' },
    { id: 3, label: 'Ticket médio', badge: '+4,6%', value: 'R$ 74,20', note: '+R$ 3,20 em relação ao mês anterior' },
    { id: 4, label: 'Itens em estoque', badge: '1.284 itens', value: '87%', note: '12 itens em baixo estoque precisam de reabastecimento' }
]

export const salesChart = {
    title: 'Quantidade de vendas',
    badge: '+8,1% vs mês anterior',
    subtitle: 'Volume de pedidos por dia no período selecionado',
    scale: ['150', '120', '90', '60', '30', '0'],
    max: 150,
    bars: [
        { label: 'Seg', value: 52 },
        { label: 'Ter', value: 78 },
        { label: 'Qua', value: 102 },
        { label: 'Qui', value: 128 },
        { label: 'Sex', value: 98 },
        { label: 'Sáb', value: 70 },
        { label: 'Dom', value: 45 }
    ]
}

export const revenueChart = {
    title: 'Receita por restaurante',
    badge: '5 restaurantes',
    subtitle: 'Distribuição de faturamento no período',
    scale: ['R$ 80k', 'R$ 60k', 'R$ 40k', 'R$ 20k', 'R$ 0'],
    max: 80,
    bars: [
        { label: 'Sabor', value: 22 },
        { label: 'Click', value: 38 },
        { label: 'Toris', value: 56 },
        { label: 'Urach', value: 72 },
        { label: 'Wolf', value: 52 }
    ]
}
