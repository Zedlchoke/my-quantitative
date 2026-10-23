"""G7-i PDF extraction boundary: only the named matchup's two teams."""
from research.papertrade_exec import ai_research as R


def test_official_pdf_extracts_exact_two_teams_and_statuses():
    text = ("10/23/2026 07:00 (ET) ATL@CHA Atlanta Hawks "
            "Player A Out Injury/Illness - Knee "
            "Charlotte Hornets Player B Questionable Ankle "
            "08:00 (ET) TOR@WAS Toronto Raptors "
            "Bittle, Nate Out Injury/Illness - Right Foot "
            "Washington Wizards Dybantsa, AJ Out Injury/Illness - Ankle "
            "09:00 (ET) DET@MIA Detroit Pistons Player C Out "
            "Miami Heat Player D Available")
    sections = R._official_pdf_sections(text, "Washington Wizards",
                                        "Toronto Raptors")
    assert "Dybantsa, AJ Out" in sections["HOME"]
    assert "Bittle, Nate Out" in sections["AWAY"]
    assert "Player C" not in str(sections)
    assert R._official_pdf_sections(text, "Washington Wizards",
                                    "Atlanta Hawks") == {}
