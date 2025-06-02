from app import create_app
from app.models import db, User, Plan, Server # Import models and db instance
import click

app = create_app()

@app.cli.command("init-db")
def init_db_command():
    """Clears existing data and creates new tables."""
    with app.app_context():
        db.drop_all() # Optional: clear all existing tables first
        db.create_all()
    click.echo("Initialized the database.")

@app.cli.command("populate-plans")
def populate_plans_command():
    """Populates the database with predefined subscription plans."""
    plans_data = [
        {
            "name": "Free Plan", "price_monthly": 0, "price_yearly": 0, 
            "ram_gb": 6, "disk_gb": 100, "time_limit_hours": 3,
            "details": "Basic features, 3-hour session limit, community support."
        },
        {
            "name": "Beginner Plan", "price_monthly": 30, "price_yearly": 340,
            "ram_gb": 12, "disk_gb": 150, "time_limit_hours": 4,
            "details": "More resources, 4-hour session limit, email support."
        },
        {
            "name": "Pro Plan", "price_monthly": 70, "price_yearly": 840,
            "ram_gb": 16, "disk_gb": 400, "time_limit_hours": 12,
            "details": "Advanced features, 12-hour session limit, priority support."
        },
        {
            "name": "Ultimate+ Plan", "price_monthly": 90, "price_yearly": 1000,
            "ram_gb": 32, "disk_gb": 1000, "time_limit_hours": None, # No limit
            "details": "All features, no session limits, dedicated support, 1TB storage."
        },
    ]

    with app.app_context():
        added_count = 0
        existing_count = 0
        for plan_info in plans_data:
            existing_plan = Plan.query.filter_by(name=plan_info["name"]).first()
            if not existing_plan:
                new_plan = Plan(
                    name=plan_info["name"],
                    price_monthly=plan_info["price_monthly"],
                    price_yearly=plan_info["price_yearly"],
                    ram_gb=plan_info["ram_gb"],
                    disk_gb=plan_info["disk_gb"],
                    time_limit_hours=plan_info["time_limit_hours"],
                    details=plan_info["details"]
                )
                db.session.add(new_plan)
                added_count += 1
            else:
                existing_count += 1
        
        if added_count > 0:
            db.session.commit()
            click.echo(f"Added {added_count} new plan(s).")
        
        if existing_count > 0:
            click.echo(f"{existing_count} plan(s) already existed.")
        
        if added_count == 0 and existing_count == len(plans_data):
             click.echo("All plans already exist in the database.")
        elif added_count == 0 and existing_count == 0 and len(plans_data) > 0 : # Should not happen if plans_data is not empty
             click.echo("No plans defined in the command.")


if __name__ == '__main__':
    app.run(debug=True)
