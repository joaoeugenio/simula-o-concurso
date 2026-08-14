import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador de Convocação de Concurso", page_icon="🎓", layout="wide")

st.title("🎓 Simulador de Convocações e Cadastro Reserva")
st.markdown("Calcule a ordem unificada de convocação respeitando as cotas de **PPP** e **PCD** conforme o edital.")

# --- REGRA DE ALTERNÂNCIA OFICIAL ---
def obter_tipo_vaga(posicao):
    """
    PCD: Posições 5, 21, 41, 61, 81... (a cada 20 admissões)
    PPP: Posições 3, 8, 13, 18, 23, 28, 33, 38, 43, 48... (a cada 5 admissões)
    AC: Demais posições
    """
    if posicao in [5, 21, 41, 61, 81, 101, 121, 141, 161, 181, 201]:
        return 'PCD'
    elif (posicao % 5 == 3):
        return 'PPP'
    else:
        return 'AC'

# --- LÓGICA DE SIMULAÇÃO DE CONVOCAÇÃO ---
def simular_convocacoes(df_ac, df_ppp, df_pcd, total_vagas):
    convocados = []
    
    fila_ac = df_ac.copy().to_dict('records') if not df_ac.empty else []
    fila_ppp = df_ppp.copy().to_dict('records') if not df_ppp.empty else []
    fila_pcd = df_pcd.copy().to_dict('records') if not df_pcd.empty else []
    
    ja_convocados_ids = set()

    for num_chamada in range(1, total_vagas + 1):
        tipo_vaga = obter_tipo_vaga(num_chamada)
        candidato_escolhido = None

        if tipo_vaga == 'PCD':
            while fila_pcd:
                cand = fila_pcd.pop(0)
                if cand['Nome'] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break
            if not candidato_escolhido:
                tipo_vaga = 'AC (Sobra PCD)'

        elif tipo_vaga == 'PPP':
            while fila_ppp:
                cand = fila_ppp.pop(0)
                if cand['Nome'] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break
            if not candidato_escolhido:
                tipo_vaga = 'AC (Sobra PPP)'

        if 'AC' in tipo_vaga:
            while fila_ac:
                cand = fila_ac.pop(0)
                if cand['Nome'] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break

        if candidato_escolhido:
            ja_convocados_ids.add(candidato_escolhido['Nome'])
            convocados.append({
                "Nº Convocação": num_chamada,
                "Nome": candidato_escolhido['Nome'],
                "Modalidade Ocupada": tipo_vaga,
                "Posição AC Original": candidato_escolhido.get('Pos_AC', '-'),
                "Posição PPP Original": candidato_escolhido.get('Pos_PPP', '-'),
                "Posição PCD Original": candidato_escolhido.get('Pos_PCD', '-')
            })

    return pd.DataFrame(convocados)

# --- INTERFACE ---
st.sidebar.header("⚙️ Configurações da Simulação")
arquivo_carregado = st.sidebar.file_uploader("Envie a planilha de classificação (.xlsx ou .csv)", type=["xlsx", "csv"])
total_vagas_simular = st.sidebar.number_input("Quantidade de convocações a simular:", min_value=1, max_value=300, value=30, step=1)

if arquivo_carregado:
    try:
        df_geral = pd.read_csv(arquivo_carregado) if arquivo_carregado.name.endswith('.csv') else pd.read_excel(arquivo_carregado)

        st.subheader("📊 Pré-visualização dos Dados Enviados")
        st.dataframe(df_geral.head(), use_container_width=True)

        df_ac = df_geral[df_geral['Pos_AC'].notnull()].sort_values('Pos_AC')
        df_ppp = df_geral[df_geral['Pos_PPP'].notnull()].sort_values('Pos_PPP') if 'Pos_PPP' in df_geral.columns else pd.DataFrame()
        df_pcd = df_geral[df_geral['Pos_PCD'].notnull()].sort_values('Pos_PCD') if 'Pos_PCD' in df_geral.columns else pd.DataFrame()

        if st.sidebar.button("🚀 Simular Convocação"):
            df_resultado = simular_convocacoes(df_ac, df_ppp, df_pcd, total_vagas_simular)
            
            st.success(f"Simulação concluída com sucesso para {len(df_resultado)} convocações!")
            st.subheader("📋 Lista Final de Convocação Unificada")
            st.dataframe(df_resultado, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                ult_ac = df_resultado[df_resultado['Modalidade Ocupada'].str.contains('AC')]['Posição AC Original'].max()
                st.metric("Alcançado na Ampla (AC)", f"Até {int(ult_ac)}º" if pd.notnull(ult_ac) else "Nenhum")
            with col2:
                ult_ppp = df_resultado[df_resultado['Modalidade Ocupada'] == 'PPP']['Posição PPP Original'].max()
                st.metric("Alcançado em PPP", f"Até {int(ult_ppp)}º" if pd.notnull(ult_ppp) else "Nenhum")
            with col3:
                ult_pcd = df_resultado[df_resultado['Modalidade Ocupada'] == 'PCD']['Posição PCD Original'].max()
                st.metric("Alcançado em PCD", f"Até {int(ult_pcd)}º" if pd.notnull(ult_pcd) else "Nenhum")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("👋 Por favor, envie a planilha na barra lateral para iniciar a simulação.")
