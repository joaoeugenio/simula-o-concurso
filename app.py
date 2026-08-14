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
def simular_convocacoes(df_ac, df_ppp, df_pcd, total_vagas, col_nome, col_ac, col_ppp, col_pcd):
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
                if cand[col_nome] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break
            if not candidato_escolhido:
                tipo_vaga = 'AC (Sobra PCD)'

        elif tipo_vaga == 'PPP':
            while fila_ppp:
                cand = fila_ppp.pop(0)
                if cand[col_nome] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break
            if not candidato_escolhido:
                tipo_vaga = 'AC (Sobra PPP)'

        if 'AC' in tipo_vaga:
            while fila_ac:
                cand = fila_ac.pop(0)
                if cand[col_nome] not in ja_convocados_ids:
                    candidato_escolhido = cand
                    break

        if candidato_escolhido:
            ja_convocados_ids.add(candidato_escolhido[col_nome])
            convocados.append({
                "Nº Convocação": num_chamada,
                "Nome": candidato_escolhido[col_nome],
                "Modalidade Ocupada": tipo_vaga,
                "Posição AC Original": candidato_escolhido.get(col_ac, '-'),
                "Posição PPP Original": candidato_escolhido.get(col_ppp, '-') if col_ppp else '-',
                "Posição PCD Original": candidato_escolhido.get(col_pcd, '-') if col_pcd else '-'
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

        st.sidebar.markdown("---")
        st.sidebar.subheader("📌 Mapeamento de Colunas")
        colunas = list(df_geral.columns)

        # Mapeamento automático inteligente
        col_nome_def = next((c for c in colunas if 'nome' in c.lower() or 'candidato' in c.lower()), colunas[0])
        col_ac_def = next((c for c in colunas if 'ac' in c.lower() or 'ampla' in c.lower() or 'geral' in c.lower()), colunas[0])
        col_ppp_def = next((c for c in colunas if 'ppp' in c.lower() or 'cota' in c.lower() or 'negro' in c.lower() or 'pardo' in c.lower()), None)
        col_pcd_def = next((c for c in colunas if 'pcd' in c.lower() or 'defic' in c.lower()), None)

        col_nome = st.sidebar.selectbox("Coluna do Nome:", colunas, index=colunas.index(col_nome_def))
        col_ac = st.sidebar.selectbox("Coluna Classificação AC:", colunas, index=colunas.index(col_ac_def))
        
        opcoes_cota = ["Nenhuma / Não possui"] + colunas
        idx_ppp = opcoes_cota.index(col_ppp_def) if col_ppp_def in opcoes_cota else 0
        idx_pcd = opcoes_cota.index(col_pcd_def) if col_pcd_def in opcoes_cota else 0
        
        sel_ppp = st.sidebar.selectbox("Coluna Classificação PPP (Opcional):", opcoes_cota, index=idx_ppp)
        sel_pcd = st.sidebar.selectbox("Coluna Classificação PCD (Opcional):", opcoes_cota, index=idx_pcd)

        col_ppp = None if sel_ppp == "Nenhuma / Não possui" else sel_ppp
        col_pcd = None if sel_pcd == "Nenhuma / Não possui" else sel_pcd

        if st.sidebar.button("🚀 Simular Convocação"):
            df_ac = df_geral[pd.to_numeric(df_geral[col_ac], errors='coerce').notnull()].copy()
            df_ac[col_ac] = pd.to_numeric(df_ac[col_ac])
            df_ac = df_ac.sort_values(col_ac)

            df_ppp = pd.DataFrame()
            if col_ppp:
                df_ppp = df_geral[pd.to_numeric(df_geral[col_ppp], errors='coerce').notnull()].copy()
                df_ppp[col_ppp] = pd.to_numeric(df_ppp[col_ppp])
                df_ppp = df_ppp.sort_values(col_ppp)

            df_pcd = pd.DataFrame()
            if col_pcd:
                df_pcd = df_geral[pd.to_numeric(df_geral[col_pcd], errors='coerce').notnull()].copy()
                df_pcd[col_pcd] = pd.to_numeric(df_pcd[col_pcd])
                df_pcd = df_pcd.sort_values(col_pcd)

            df_resultado = simular_convocacoes(df_ac, df_ppp, df_pcd, total_vagas_simular, col_nome, col_ac, col_ppp, col_pcd)
            
            st.success(f"Simulação concluída com sucesso para {len(df_resultado)} convocações!")
            st.subheader("📋 Lista Final de Convocação Unificada")
            st.dataframe(df_resultado, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                ult_ac = df_resultado[df_resultado['Modalidade Ocupada'].str.contains('AC')]['Posição AC Original'].max()
                st.metric("Alcançado na Ampla (AC)", f"Até {int(ult_ac)}º" if pd.notnull(ult_ac) and ult_ac != '-' else "Nenhum")
            with col2:
                ult_ppp = df_resultado[df_resultado['Modalidade Ocupada'] == 'PPP']['Posição PPP Original'].max()
                st.metric("Alcançado em PPP", f"Até {int(ult_ppp)}º" if pd.notnull(ult_ppp) and ult_ppp != '-' else "Nenhum")
            with col3:
                ult_pcd = df_resultado[df_resultado['Modalidade Ocupada'] == 'PCD']['Posição PCD Original'].max()
                st.metric("Alcançado em PCD", f"Até {int(ult_pcd)}º" if pd.notnull(ult_pcd) and ult_pcd != '-' else "Nenhum")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("👋 Por favor, envie a planilha na barra lateral para iniciar a simulação.")
