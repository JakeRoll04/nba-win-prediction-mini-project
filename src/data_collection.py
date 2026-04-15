import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder


def fetch_recent_team_games(team_name, season="2023-24", season_type="Regular Season", max_games=50):
    """
    Fetch recent NBA team-level game data and return it as a clean DataFrame.

    Parameters:
        team_name (str): Full team name or abbreviation, e.g. "Los Angeles Lakers" or "LAL".
        season (str): Season string, e.g. "2023-24".
        season_type (str): NBA season type, usually "Regular Season" or "Playoffs".
        max_games (int): Maximum number of most recent games to return.

    Returns:
        pandas.DataFrame: Cleaned game-level team data with columns:
            ["team_id", "team_name", "game_id", "game_date", "opponent",
             "location", "points", "opponent_points", "win_loss"].
    """
    if max_games <= 0:
        raise ValueError("max_games must be a positive integer")

    # Try abbreviation first
    team = teams.find_team_by_abbreviation(team_name.upper())
    if not team:
        # Fall back to partial/full-name match
        team = next(
            (t for t in teams.get_teams() if team_name.lower() in t["full_name"].lower()),
            None,
        )

    if not team:
        raise ValueError(f"Could not find an NBA team matching '{team_name}'")

    team_id = team["id"]
    team_full_name = team["full_name"]

    finder = leaguegamefinder.LeagueGameFinder(
        player_or_team_abbreviation="T",
        team_id_nullable=team_id,
        season_nullable=season,
        season_type_nullable=season_type,
    )

    games = finder.get_data_frames()[0]

    if games.empty:
        return pd.DataFrame(
            columns=[
                "team_id",
                "team_name",
                "game_id",
                "game_date",
                "opponent",
                "location",
                "points",
                "opponent_points",
                "win_loss",
            ]
        )

    games = games[
        [
            "GAME_ID",
            "GAME_DATE",
            "MATCHUP",
            "WL",
            "PTS",
            "PLUS_MINUS",
        ]
    ].copy()

    games = games.rename(
        columns={
            "GAME_ID": "game_id",
            "GAME_DATE": "game_date",
            "MATCHUP": "matchup",
            "WL": "win_loss",
            "PTS": "points",
            "PLUS_MINUS": "plus_minus",
        }
    )

    games["team_id"] = team_id
    games["team_name"] = team_full_name

    games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce")
    games["points"] = pd.to_numeric(games["points"], errors="coerce")
    games["plus_minus"] = pd.to_numeric(games["plus_minus"], errors="coerce")

    # Since plus_minus = team points - opponent points
    games["opponent_points"] = games["points"] - games["plus_minus"]

    games["location"] = games["matchup"].apply(
        lambda x: "Home" if isinstance(x, str) and "vs." in x else "Away"
    )

    games["opponent"] = games["matchup"].apply(
        lambda x: x.split()[-1] if isinstance(x, str) else None
    )

    games = games[
        [
            "team_id",
            "team_name",
            "game_id",
            "game_date",
            "opponent",
            "location",
            "points",
            "opponent_points",
            "win_loss",
        ]
    ]

    games = games.dropna(subset=["game_date", "points", "opponent_points", "win_loss"])
    games = games.sort_values("game_date", ascending=False).head(max_games).reset_index(drop=True)

    return games