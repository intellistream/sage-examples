from sage.apps.patent_landscape_mapper import (
    build_demo_patent_corpus,
    print_patent_landscape_report,
    run_patent_landscape_mapper_pipeline,
)


def test_patent_landscape_pipeline_returns_report() -> None:
    report = run_patent_landscape_mapper_pipeline()

    assert report.patent_count == 12
    assert report.assignee_count >= 10
    assert len(report.theme_clusters) == 4
    assert report.whitespace_opportunities
    assert report.watchlist_patents
    assert "Mapped 12 patents" in report.summary


def test_patent_landscape_clusters_have_graph_support() -> None:
    report = run_patent_landscape_mapper_pipeline()

    node_types = {node.node_type for node in report.graph_nodes}
    edge_relations = {edge.relation for edge in report.graph_edges}

    assert {"theme", "patent", "assignee"}.issubset(node_types)
    assert "maps_to_theme" in edge_relations
    assert "owns_patent" in edge_relations


def test_patent_landscape_focus_keywords_surface_cold_chain_opportunity() -> None:
    report = run_patent_landscape_mapper_pipeline(
        focus_keywords=["cold chain", "biologics logistics", "sterile storage"],
    )

    labels = [cluster.label for cluster in report.theme_clusters]
    assert any("Cold Chain" in label or "Biologics" in label for label in labels)
    assert any(
        "cold chain" in " ".join(item.target_keywords).lower() or "biologics" in item.title.lower()
        for item in report.whitespace_opportunities
    )


def test_patent_landscape_console_renderer(capsys) -> None:
    report = run_patent_landscape_mapper_pipeline(patents=build_demo_patent_corpus())

    print_patent_landscape_report(report, top_opportunities=2)

    captured = capsys.readouterr()
    assert "SAGE Patent Landscape Mapper" in captured.out
    assert "Whitespace Opportunities" in captured.out
