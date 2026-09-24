# src/reporting/timeline_html_generator.py
"""
Gerador de Painel Interativo HTML para Reconstituição Cronológica de Inquéritos
e Grafo de Atores Processuais (SICAI Forensic Timeline Viewer).
"""
import json
from typing import Dict, Any, List
from src.quality.schemas import InquiryTimelineReport

def generate_interactive_timeline_html(
    report: InquiryTimelineReport,
    actors_graph: Dict[str, Dict[str, Any]],
    output_path: str
) -> str:
    """Gera um arquivo HTML autônomo e interativo com linha do tempo e catálogo de atores."""

    events_data = []
    for ev in report.events:
        events_data.append({
            "event_date": ev.event_date or "Data Indeterminada",
            "raw_date_text": ev.raw_date_text or "",
            "event_type": ev.event_type,
            "headline": ev.headline,
            "description": ev.description,
            "actors": [{"name": a.name, "role": a.role, "organization": a.organization or ""} for a in ev.actors],
            "page_number": ev.page_number,
            "verbatim_quote": ev.verbatim_quote
        })

    events_json = json.dumps(events_data, ensure_ascii=False)
    actors_json = json.dumps(actors_graph, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SICAI - Reconstituição Cronológica e Atores do Inquérito</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-purple: #a855f7;
            --accent-green: #22c55e;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .badge-sicai {{
            background: #0284c7;
            color: #fff;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            color: #fff;
        }}
        .header-meta {{
            display: flex;
            gap: 24px;
            color: var(--text-muted);
            font-size: 14px;
            flex-wrap: wrap;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }}
        .stat-val {{
            font-size: 28px;
            font-weight: 700;
            color: var(--accent-blue);
        }}
        .stat-lbl {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        .nav-tabs {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 15px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab-btn.active {{
            background: #0284c7;
            color: #fff;
        }}
        .controls {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .search-box {{
            flex: 1;
            min-width: 280px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 16px;
            color: #fff;
            font-size: 14px;
        }}
        .search-box:focus {{
            outline: 2px solid var(--accent-blue);
        }}
        /* Timeline styling */
        .timeline-container {{
            position: relative;
            padding-left: 32px;
        }}
        .timeline-container::before {{
            content: '';
            position: absolute;
            left: 11px;
            top: 10px;
            bottom: 10px;
            width: 2px;
            background: var(--border-color);
        }}
        .timeline-item {{
            position: relative;
            margin-bottom: 24px;
        }}
        .timeline-dot {{
            position: absolute;
            left: -27px;
            top: 6px;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: var(--accent-blue);
            border: 3px solid var(--bg-primary);
            box-shadow: 0 0 10px var(--accent-blue);
        }}
        .timeline-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.15s, border-color 0.15s;
        }}
        .timeline-card:hover {{
            border-color: var(--accent-blue);
        }}
        .event-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .event-date {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-blue);
        }}
        .badge-type {{
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .event-title {{
            font-size: 17px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #fff;
        }}
        .event-desc {{
            color: #cbd5e1;
            font-size: 14px;
            margin-bottom: 14px;
        }}
        .actors-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .actor-pill {{
            background: #334155;
            color: #e2e8f0;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .actor-role {{
            font-weight: 700;
            color: var(--accent-amber);
        }}
        .quote-box {{
            background: rgba(15, 23, 42, 0.8);
            border-left: 3px solid var(--accent-purple);
            padding: 10px 14px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #cbd5e1;
            margin-top: 10px;
        }}
        .page-badge {{
            background: rgba(168, 85, 247, 0.15);
            color: var(--accent-purple);
            border: 1px solid rgba(168, 85, 247, 0.3);
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        /* Actors roster styling */
        .actors-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        .actor-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
        }}
        .actor-name {{
            font-size: 18px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 6px;
        }}
        .actor-meta {{
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 12px;
        }}
        .actor-actions-list {{
            font-size: 12px;
            color: #cbd5e1;
            border-top: 1px solid var(--border-color);
            padding-top: 10px;
            max-height: 180px;
            overflow-y: auto;
        }}
        .actor-action-item {{
            margin-bottom: 6px;
            padding-bottom: 6px;
            border-bottom: 1px dashed rgba(51, 65, 85, 0.5);
        }}
    </style>
</head>
<body>

    <div class="header">
        <div class="header-top">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="badge-sicai">SICAI FORENSIC AI</span>
                <h1>Reconstituição Cronológica e Grafo de Atores</h1>
            </div>
            <div>
                <button onclick="window.print()" class="tab-btn" style="border: 1px solid var(--border-color)">Imprimir / Exportar PDF</button>
            </div>
        </div>
        <div class="header-meta">
            <div><strong>Peça dos Autos:</strong> {report.document_name}</div>
            <div><strong>Caso / Inquérito:</strong> {report.case_id}</div>
            <div><strong>Total de Páginas Analisadas:</strong> {report.total_pages_analyzed}</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val" id="totalEventsCount">{len(report.events)}</div>
                <div class="stat-lbl">Fatos & Decisões Mapeados</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" id="totalActorsCount">{len(actors_graph)}</div>
                <div class="stat-lbl">Atores Processuais Identificados</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{report.events[0].event_date if report.events and report.events[0].event_date else 'N/A'}</div>
                <div class="stat-lbl">Primeiro Marco Detectado (T0)</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{report.events[-1].event_date if report.events and report.events[-1].event_date else 'N/A'}</div>
                <div class="stat-lbl">Último Marco Detectado (Tn)</div>
            </div>
        </div>
    </div>

    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('timeline')">Linha do Tempo Fática ({len(report.events)})</button>
        <button class="tab-btn" onclick="switchTab('actors')">Grafo de Atores Processuais ({len(actors_graph)})</button>
    </div>

    <div class="controls">
        <input type="text" id="searchInput" class="search-box" placeholder="Buscar por ator, ato (ex: 'busca e apreensão', 'decisão'), data ou palavra-chave..." oninput="filterContent()">
    </div>

    <!-- TAB 1: LINHA DO TEMPO -->
    <div id="tabTimeline" class="timeline-container">
        <!-- Renderizado dinamicamente via JS -->
    </div>

    <!-- TAB 2: ATORES PROCESSUAIS -->
    <div id="tabActors" class="actors-grid" style="display: none;">
        <!-- Renderizado dinamicamente via JS -->
    </div>

    <script>
        const eventsData = {events_json};
        const actorsData = {actors_json};

        let activeTab = 'timeline';

        function switchTab(tab) {{
            activeTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            if (tab === 'timeline') {{
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
                document.getElementById('tabTimeline').style.display = 'block';
                document.getElementById('tabActors').style.display = 'none';
            }} else {{
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
                document.getElementById('tabTimeline').style.display = 'none';
                document.getElementById('tabActors').style.display = 'grid';
            }}
            filterContent();
        }}

        function renderTimeline(events) {{
            const container = document.getElementById('tabTimeline');
            if (events.length === 0) {{
                container.innerHTML = '<div style="color: #94a3b8; padding: 20px;">Nenhum fato encontrado para os critérios de busca.</div>';
                return;
            }}
            container.innerHTML = events.map(ev => `
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-card">
                        <div class="event-header">
                            <div>
                                <span class="event-date">📅 ${{ev.event_date || 'Data não especificada'}}</span>
                                ${{ev.raw_date_text ? `<span style="color: #94a3b8; font-size: 12px; margin-left: 8px;">(${{ev.raw_date_text}})</span>` : ''}}
                            </div>
                            <div>
                                <span class="badge-type">${{ev.event_type}}</span>
                                <span class="page-badge">Fls. ${{ev.page_number}}</span>
                            </div>
                        </div>
                        <div class="event-title">${{ev.headline}}</div>
                        <div class="event-desc">${{ev.description}}</div>
                        <div class="actors-pills">
                            ${{ev.actors.map(a => `
                                <span class="actor-pill">
                                    <span class="actor-role">${{a.role}}:</span>
                                    <span>${{a.name}}</span>
                                    ${{a.organization ? `<span style="color: #94a3b8;">(${{a.organization}})</span>` : ''}}
                                </span>
                            `).join('')}}
                        </div>
                        <div class="quote-box">
                            <span style="color: var(--accent-purple); font-weight: 700;">PROVA TEXTUAL (GROUND TRUTH):</span><br>
                            "${{ev.verbatim_quote}}"
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function renderActors(actors) {{
            const container = document.getElementById('tabActors');
            const entries = Object.values(actors);
            if (entries.length === 0) {{
                container.innerHTML = '<div style="color: #94a3b8; padding: 20px;">Nenhum ator encontrado.</div>';
                return;
            }}
            container.innerHTML = entries.map(a => `
                <div class="actor-card">
                    <div class="actor-name">${{a.name}}</div>
                    <div class="actor-meta">
                        <div><strong>Cargos:</strong> ${{a.roles.join(', ') || 'N/A'}}</div>
                        <div><strong>Órgãos:</strong> ${{a.organizations.join(', ') || 'N/A'}}</div>
                        <div><strong>Total de Aparições:</strong> ${{a.appearances_count}} atos</div>
                        <div><strong>Páginas dos Autos:</strong> Fls. ${{a.pages.join(', ')}}</div>
                    </div>
                    <div class="actor-actions-list">
                        <strong>Atos e Participações:</strong>
                        ${{a.actions.map(act => `
                            <div class="actor-action-item">
                                <span style="color: var(--accent-blue); font-weight: 600;">[${{act.date || 'Data N/D'}}]</span>
                                ${{act.headline}} (Fls. ${{act.page}})
                            </div>
                        `).join('')}}
                    </div>
                </div>
            `).join('');
        }}

        function filterContent() {{
            const query = document.getElementById('searchInput').value.toLowerCase().trim();

            if (activeTab === 'timeline') {{
                const filtered = eventsData.filter(ev => {{
                    const matchText = (ev.headline + ' ' + ev.description + ' ' + ev.event_date + ' ' + ev.verbatim_quote).toLowerCase();
                    const matchActors = ev.actors.some(a => (a.name + ' ' + a.role + ' ' + a.organization).toLowerCase().includes(query));
                    return matchText.includes(query) || matchActors;
                }});
                renderTimeline(filtered);
            }} else {{
                const filteredActors = {{}};
                for (const [key, actor] of Object.entries(actorsData)) {{
                    const match = (actor.name + ' ' + actor.roles.join(' ') + ' ' + actor.organizations.join(' ')).toLowerCase();
                    if (match.includes(query)) {{
                        filteredActors[key] = actor;
                    }}
                }}
                renderActors(filteredActors);
            }}
        }}

        // Inicialização inicial
        renderTimeline(eventsData);
        renderActors(actorsData);
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
