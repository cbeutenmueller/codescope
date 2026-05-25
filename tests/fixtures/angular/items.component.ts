import { Component, OnInit } from '@angular/core';
import { ItemService } from '../services/item.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-items',
  template: `<ul><li *ngFor="let item of items">{{ item.name }}</li></ul>`,
})
export class ItemsComponent implements OnInit {
  items: any[] = [];
  private subscription: Subscription;

  constructor(private itemService: ItemService) {}

  ngOnInit(): void {
    // Smell: subscription not unsubscribed in ngOnDestroy
    this.subscription = this.itemService.getItems().subscribe(items => {
      this.items = items;
    });
  }
}
