from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect
from datetime import datetime, timedelta

from Movimentacoes.models import Movimentacoes
from core.models import Uteis
from .models import Pessoas, Financeiro


def gerar_financeiro(request):
    # Estanciando classes
    movimentacoes = Movimentacoes()
    pessoas = Pessoas()
    uteis = Uteis()
    financeiro = Financeiro()

    # Recebendo valores e tratando
    id = request.POST['id']
    conta = request.POST['conta']
    centro_custo = request.POST['centro_custo']
    planos_contas = request.POST['planos_contas']

    # Recebendo valores de entrada e tratando
    entrada = request.POST['entrada']
    entrada = entrada.replace(',', '.')
    entrada = float(entrada)

    # Recebendo valores e tratando
    parcelas = int(request.POST['parcelas'])

    # Recebendo datas de vecimento
    vencimentos = request.POST.getlist('vencimentos[]')

    # Fazendo busca das prevendas
    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_query_convertida('False')
    cursor = movimentacoes.execute_one()


    if 'InformacoesPesquisa' in cursor and cursor['Situacao']['Codigo'] == 1:
        data = datetime.now()
        database = uteis.conexao
        emitente = pessoas.get_emitente()

        # Modificando Pre-Venda para criar atrelar parcelas financeiras
        cursor['PagamentoRecebimento'] = {'_t': 'Recebimento', 'Parcelas': []}

        # Modificar para status aprovado
        cursor['Situacao'] = {
            '_t': [
                'SituacaoMovimentacao',
                'Aprovado'
            ],
            'Codigo': 8,
            'Descricao': 'Aprovado',
            'Cor': '#006400',
            'DescricaoComando': 'Tornar pendente'
        }

        # Pegando total da nota com descontos
        cursor = uteis.total_venda(cursor)
        cursor['liquido'] = cursor['liquido'] - entrada

        # Configurando informações de pesquisa
        informacoes_pesquisa = []
        informacoes_pesquisa.extend(cursor['InformacoesPesquisa'])
        informacoes_pesquisa.append('pre-venda ' + str(cursor['Numero']))

        # Tratando valores da parcela
        valor_parcela = cursor['liquido'] / parcelas
        valor_parcela = float('%.2f' % valor_parcela)

        # Reconfigurando contador pra reutilizar
        x = 0

        # Verificando se tem entradas
        if entrada > 0:
            parcelas = parcelas+1
            x = x+1

            cursor['PagamentoRecebimento']['Parcelas'].append({
                '_t': ['ParcelaRecebimento', 'ParcelaRecebimentoManual'],
                'InformacoesPesquisa': informacoes_pesquisa,
                'Versao': '736794.19:26:22.9976483',
                'Ativo': True,
                'Ordem': x,
                'Descricao': 'PRE-VENDA ' + str(cursor['Numero']) + ' - ' + str(x),
                'Documento': str(cursor['Numero']),
                'PessoaReferencia': cursor['Pessoa']['PessoaReferencia'],
                'Vencimento': data,
                'Historico': [
                    {
                        '_t': 'HistoricoAguardando',
                        'Valor': entrada,
                        'EspeciePagamento': {
                            '_t': 'EspeciePagamentoECF',
                            'Codigo': 1,
                            'Descricao': 'Dinheiro',
                            'EspecieRecebimento': {
                                '_t': 'Dinheiro'
                            }
                        },
                        'PlanoContaCodigoUnico': planos_contas,
                        'CentroCustoCodigoUnico': centro_custo,
                        'ContaReferencia': ObjectId(conta),
                        'EmpresaReferencia': emitente['_id'],
                        'Data': data,
                        'ChequeReferencia': ObjectId('000000000000000000000000')
                    },
                    {
                        '_t': 'HistoricoPendente',
                        'Valor': entrada,
                        'EspeciePagamento': {
                            '_t': 'EspeciePagamentoECF',
                            'Codigo': 1,
                            'Descricao': 'Dinheiro',
                            'EspecieRecebimento': {
                                '_t': 'Dinheiro'
                            }
                        },
                        'PlanoContaCodigoUnico': planos_contas,
                        'CentroCustoCodigoUnico': centro_custo,
                        'ContaReferencia': ObjectId(conta),
                        'EmpresaReferencia': emitente['_id'],
                        'NomeUsuario': 'Usuário Administrador',
                        'Data': data,
                        'ChequeReferencia': ObjectId('000000000000000000000000')
                    },
                    {
                        '_t': 'HistoricoQuitado',
                        'Valor': entrada,
                        'EspeciePagamento': {
                            '_t': 'EspeciePagamentoECF',
                            'Codigo': 1,
                            'Descricao': 'Dinheiro',
                            'EspecieRecebimento': {
                                '_t': 'Dinheiro'
                            }
                        },
                        'PlanoContaCodigoUnico': planos_contas,
                        'CentroCustoCodigoUnico': centro_custo,
                        'ContaReferencia': ObjectId(conta),
                        'EmpresaReferencia': emitente['_id'],
                        'NomeUsuario': 'Usuário Administrador',
                        'Data': data,
                        'ChequeReferencia': ObjectId('000000000000000000000000'),
                        'Desconto': 0.0,
                        'Acrescimo': 0.0,
                        'DataQuitacao': data
                    }
                ],
                'Situacao': {
                    '_t': 'Quitada',
                    'Codigo': 3
                },
                'ContaReferencia': ObjectId(conta),
                'EmpresaReferencia': emitente['_id'],
                'NomeUsuario': 'Usuário Administrador',
                'DataQuitacao': data,
                'AcrescimoInformado': 0.0,
                'DescontoInformado': 0.0,
            })

        if valor_parcela > 0:
            y = 0
            while x < parcelas:
                cursor['PagamentoRecebimento']['Parcelas'].append({
                    '_t': ['ParcelaRecebimento', 'ParcelaRecebimentoManual'],
                    'InformacoesPesquisa': informacoes_pesquisa,
                    'Versao': '736794.19:26:22.9976483',
                    'Ativo': True,
                    'Ordem': x + 1,
                    'Descricao': 'PRE-VENDA ' + str(cursor['Numero']) + ' - ' + str(x + 1),
                    'Documento': str(cursor['Numero']),
                    'PessoaReferencia': cursor['Pessoa']['PessoaReferencia'],
                    'Vencimento': datetime.strptime(vencimentos[y], '%Y-%m-%d'),
                    'Historico': [
                        {
                            '_t': 'HistoricoAguardando',
                            'Valor': valor_parcela,
                            'EspeciePagamento': {
                                '_t': 'EspeciePagamentoECF',
                                'Codigo': 1,
                                'Descricao': 'Dinheiro',
                                'EspecieRecebimento': {
                                    '_t': 'Dinheiro'
                                }
                            },
                            'PlanoContaCodigoUnico': planos_contas,
                            'CentroCustoCodigoUnico': centro_custo,
                            'ContaReferencia': ObjectId(conta),
                            'EmpresaReferencia': emitente['_id'],
                            'Data': data,
                            'ChequeReferencia': ObjectId('000000000000000000000000')
                        },
                        {
                            '_t': 'HistoricoPendente',
                            'Valor': valor_parcela,
                            'EspeciePagamento': {
                                '_t': 'EspeciePagamentoECF',
                                'Codigo': 1,
                                'Descricao': 'Dinheiro',
                                'EspecieRecebimento': {
                                    '_t': 'Dinheiro'
                                }
                            },
                            'PlanoContaCodigoUnico': planos_contas,
                            'CentroCustoCodigoUnico': centro_custo,
                            'ContaReferencia': ObjectId(conta),
                            'EmpresaReferencia': emitente['_id'],
                            'NomeUsuario': 'Usuário Administrador',
                            'Data': data,
                            'ChequeReferencia': ObjectId('000000000000000000000000')
                        }
                    ],
                    'Situacao': {
                        '_t': 'Pendente',
                        'Codigo': 1
                    },
                    'ContaReferencia': ObjectId(conta),
                    'EmpresaReferencia': emitente['_id'],
                    'NomeUsuario': 'Usuário Administrador',
                    'DataQuitacao': '0001-01-01T00:00:00.000+0000',
                    'AcrescimoInformado': 0.0,
                    'DescontoInformado': 0.0,
                })
                x = x + 1
                y = y+1


        try:
            z = 0
            # Começando procedimento de insert no banco
            for x in cursor['PagamentoRecebimento']['Parcelas']:
                # Inserindo parcelas no banco
                id_parcela = database['Recebimentos'].insert(x)

                # Consultando ID para atualizar na tabela de movimentações
                financeiro.set_query_id(id_parcela)

                # Atualizando na tabela de
                cursor['PagamentoRecebimento']['Parcelas'][z] = financeiro.execute_one()
                z = z+1

            # Configurando CFOP para não gerar financeiro
            z = 0
            for item in cursor['ItensBase']:
                cursor['ItensBase'][z]['OperacaoFiscal']['Tipo'] = 5
                z = z+1

            # Removendo totais para pode atualizar no banco
            cursor = uteis.remover_totais(cursor)

            # Removendo ID tratado para pode inserir no banco
            del cursor['id']

            # Atualizando movimentação com parcela financeira para identificação no sistema
            database['Movimentacoes'].update({'_id': cursor['_id']}, cursor)

            # Redirecionando para o Comprovante de debito
            return redirect('financeiro:comprovante_de_debito_por_movimentacao', id)
        except Exception as e:
            print(e)


def comprovante_de_debito_por_movimentacao(request, id):
    template_name = 'movimentacoes/comprovante_de_debito.html'

    # Estanciando classes
    movimentacoes = Movimentacoes()
    pessoas = Pessoas()
    financeiro = Financeiro()
    uteis = Uteis()


    # Fazendo busca das prevendas
    movimentacoes.set_query_id(id)
    cursor = movimentacoes.execute_one()

    # Inserindo informações de totais parar exibição posterior no impresso
    cursor = uteis.total_venda(cursor)

    parcelamento = []
    for x in cursor['PagamentoRecebimento']['Parcelas']:

        # Realizando busca no banco pelas parcelas atualizadas no sistema
        pago = 0
        financeiro.set_query_id(x['_id'])
        result = financeiro.execute_one()

        # Verificando quais parcelas foram quitadas
        for hist in result['Historico']:
            if 'HistoricoQuitado' in hist['_t'] or 'HistoricoQuitadoParcial' in hist['_t']:
                pago = hist['Valor']

        # Inserindo a informação de qual valor foi quitado
        parcelamento.append({'Vencimento': result['Vencimento'],
                             'Valor': result['Historico'][0]['Valor'],
                             'Pago': pago})

    # Reordenando para exibição
    parcelamento.sort(key=lambda t: t['Vencimento'])
    emitente = pessoas.get_emitente()

    # Criando a variavel context para passa dados para template
    context = {}
    context['Emitente'] = emitente
    context['Prevenda'] = cursor
    context['Data'] = datetime.now()
    context['Parcelamento'] = parcelamento

    return render(request, template_name, context)

def recibo(request):
    if request.method == 'POST':
        ids = request.POST.getlist('parcela')
        uteis = Uteis()
        pessoas = Pessoas()

        cnpj = pessoas.get_cnpj_emitente()
        nome_emitente = pessoas.get_nome_emitente()

        cnpj = '%s.%s.%s/%s-%s' % (cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])
        Emitente = {'Cnpj': cnpj, 'Nome': nome_emitente}
        recibos = {}

        for id in ids:
            financeiro = Financeiro()
            financeiro.set_query_situacao(u'Quitada')
            financeiro.set_query_id(id)
            cursor = financeiro.execute_one()
            clienteid = str(cursor['PessoaReferencia'])

            if clienteid in recibos:
                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['financeiro'].append({'Valor_Pago': valor_pago,
                                                                 'Documento': cursor['Documento'],
                                                                 'Parcela': cursor['Ordem'],
                                                                 'Data_Quitacao': cursor['DataQuitacao']})

            else:
                cliente = pessoas.get_nome(cursor['PessoaReferencia'])
                saldo_devedor = pessoas.get_saldo_devedor(cursor['PessoaReferencia'])

                recibos[clienteid] = {}
                recibos[clienteid]['financeiro'] = []
                recibos[clienteid]['Total'] = 0
                recibos[clienteid]['Total_extenso'] = ''
                recibos[clienteid]['Cliente'] = {'Nome': cliente, 'Total_devedor': saldo_devedor}

                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['financeiro'].append({'Valor_Pago': valor_pago,
                                                                 'Documento': cursor['Documento'],
                                                                 'Parcela': cursor['Ordem'],
                                                                 'Data_Quitacao': cursor['DataQuitacao']})

        for recibo in recibos:
            recibos[recibo]['Total_extenso'] = uteis.num_to_currency(
                ('%.2f' % recibos[recibo]['Total']).replace('.', ''))

        context = {'Data': datetime.now(), 'Emitente': Emitente, 'Recibos': recibos}
        return render(request, 'financeiro/recibo.html', context)

def recebidas(request):
    template_name = 'financeiro/recebidas.html'

    # Estanciando classes necessarias
    pessoas = Pessoas()
    financeiro = Financeiro()
    movimentacao = Movimentacoes()

    # Buscando parcelas na situação quitadas
    financeiro.set_query_situacao(u'Quitada')
    financeiro.set_sort_data_quitacao()
    financeiro.set_sort_vencimento()
    cursor = financeiro.execute_all()

    # Declarando variavel de listagem
    recebimentos = []

    for recebimento in cursor:
        # Localizando o nome do cliente
        recebimento['PessoaNome'] = pessoas.get_nome(recebimento['PessoaReferencia'])

        # Verificando valor pago
        for item in recebimento['Historico']:
            if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                recebimento['valor_pago'] = item['Valor']

        # Partindo procurar movimentacoes que envolva essa parcela
        movimentacao.set_query_movimentacao_por_recebimento(recebimento['_id'])
        movimentacao.set_projection_id()
        result = movimentacao.execute_one()

        # Verificando se a parcela tem movimentacao criada
        if result == None:
            recebimento['MovimentacaoID'] = 0
        else:
            recebimento['MovimentacaoID'] = result['_id']
        recebimentos.append(recebimento)

    context = {'Recebimentos': recebimentos}
    return render(request, template_name, context)

def pendentes(request):
    template_name = 'financeiro/pendentes.html'

    # Estanciando classes necessarias
    pessoas = Pessoas()
    financeiro = Financeiro()
    movimentacao = Movimentacoes()

    # Buscando parcelas na situação pendente
    financeiro.set_query_situacao(u'Pendente')
    financeiro.set_sort_vencimento()
    cursor = financeiro.execute_all()

    # Declarando variavel de listagem
    recebimentos = []

    for recebimento in cursor:
        # Localizando o nome do cliente
        recebimento['PessoaNome'] = pessoas.get_nome(recebimento['PessoaReferencia'])

        # Partindo procurar movimentacoes que envolva essa parcela
        movimentacao.set_query_movimentacao_por_recebimento(recebimento['_id'])
        movimentacao.set_projection_id()
        result = movimentacao.execute_one()

        # Verificando se a parcela tem movimentacao criada
        if result == None:
            recebimento['MovimentacaoID'] = 0
        else:
            recebimento['MovimentacaoID'] = result['_id']

        recebimentos.append(recebimento)

    context = {'recebimentos': recebimentos}
    return render(request, template_name, context)
